"""Google Fit OAuth flow and data sync."""
import logging
from datetime import datetime, timezone, timedelta
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User, FitOAuthToken
from app.models.activity import Activity
from app.utils.encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
FITNESS_BASE = "https://www.googleapis.com/fitness/v1/users/me"


def get_oauth_url() -> str:
    """Build the Google OAuth2 authorization URL."""
    scopes = [
        "https://www.googleapis.com/auth/fitness.activity.read",
        "https://www.googleapis.com/auth/fitness.body.read",
        "https://www.googleapis.com/auth/fitness.heart_rate.read",
        "https://www.googleapis.com/auth/fitness.sleep.read",
    ]
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://accounts.google.com/o/oauth2/v2/auth?{qs}"


async def exchange_code(code: str, user: User, db: Session) -> dict:
    """Exchange authorization code for tokens. Store encrypted."""
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=payload)

    if resp.status_code != 200:
        logger.error(f"Token exchange failed: {resp.text[:200]}")
        raise ValueError("Google token exchange failed")

    data = resp.json()
    access_token = data["access_token"]
    refresh_token = data.get("refresh_token", "")
    expires_in = data.get("expires_in", 3600)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    token_record = db.query(FitOAuthToken).filter(FitOAuthToken.user_id == user.id).first()
    if token_record:
        token_record.access_token = encrypt_token(access_token)
        token_record.refresh_token = encrypt_token(refresh_token) if refresh_token else token_record.refresh_token
        token_record.expires_at = expires_at
    else:
        token_record = FitOAuthToken(
            user_id=user.id,
            access_token=encrypt_token(access_token),
            refresh_token=encrypt_token(refresh_token),
            expires_at=expires_at,
        )
        db.add(token_record)
    db.commit()

    return {"status": "connected", "expires_at": expires_at.isoformat()}


async def _get_valid_token(user: User, db: Session) -> str:
    """Get a valid access token, refreshing if expired."""
    token_record = db.query(FitOAuthToken).filter(FitOAuthToken.user_id == user.id).first()
    if not token_record:
        raise ValueError("Google Fit not connected")

    now = datetime.now(timezone.utc)
    if token_record.expires_at and token_record.expires_at > now:
        return decrypt_token(token_record.access_token)

    # Refresh
    refresh_tok = decrypt_token(token_record.refresh_token)
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_tok,
        "grant_type": "refresh_token",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=payload)

    if resp.status_code != 200:
        logger.error(f"Token refresh failed: {resp.text[:200]}")
        raise ValueError("Google Fit token refresh failed")

    data = resp.json()
    new_access = data["access_token"]
    expires_in = data.get("expires_in", 3600)

    token_record.access_token = encrypt_token(new_access)
    token_record.expires_at = now + timedelta(seconds=expires_in)
    db.commit()

    return new_access


async def sync_data(user: User, db: Session, days: int = 1) -> dict:
    """Sync steps, heart rate, workouts, sleep from Google Fit."""
    access_token = await _get_valid_token(user, db)
    headers = {"Authorization": f"Bearer {access_token}"}

    now = datetime.now(timezone.utc)
    start_ms = int((now - timedelta(days=days)).timestamp() * 1000)
    end_ms = int(now.timestamp() * 1000)

    synced = {"steps": 0, "heart_rate": 0, "workouts": 0, "sleep": 0}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Steps
        steps_data = await _fetch_aggregate(client, headers, start_ms, end_ms,
                                            "com.google.step_count.delta",
                                            "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps")
        for bucket in steps_data:
            steps = bucket.get("value", 0)
            if steps > 0:
                ts = datetime.fromtimestamp(bucket["start_ms"] / 1000, tz=timezone.utc)
                act = Activity(user_id=user.id, timestamp=ts, type="steps",
                               data_json={"steps": steps}, source="google_fit")
                db.add(act)
                synced["steps"] += 1

        # Heart rate
        hr_data = await _fetch_aggregate(client, headers, start_ms, end_ms,
                                         "com.google.heart_rate.bpm",
                                         "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm")
        for bucket in hr_data:
            bpm = bucket.get("value", 0)
            if bpm > 0:
                ts = datetime.fromtimestamp(bucket["start_ms"] / 1000, tz=timezone.utc)
                act = Activity(user_id=user.id, timestamp=ts, type="heart_rate",
                               data_json={"bpm": bpm}, source="google_fit")
                db.add(act)
                synced["heart_rate"] += 1

    db.commit()

    # Trigger post-sync pipeline
    _post_sync_pipeline(user, db)

    return synced


async def _fetch_aggregate(client: httpx.AsyncClient, headers: dict,
                           start_ms: int, end_ms: int,
                           data_type: str, data_source: str) -> list[dict]:
    """Fetch aggregated fitness data from Google Fit API."""
    body = {
        "aggregateBy": [{"dataTypeName": data_type, "dataSourceId": data_source}],
        "bucketByTime": {"durationMillis": 86400000},
        "startTimeMillis": start_ms,
        "endTimeMillis": end_ms,
    }
    try:
        resp = await client.post(f"{FITNESS_BASE}/dataset:aggregate", headers=headers, json=body)
        if resp.status_code != 200:
            logger.warning(f"Fit API {data_type}: {resp.status_code}")
            return []
        data = resp.json()
        buckets = data.get("bucket", [])
        results = []
        for b in buckets:
            start = int(b.get("startTimeMillis", 0))
            for ds in b.get("dataset", []):
                for pt in ds.get("point", []):
                    for v in pt.get("value", []):
                        val = v.get("intVal") or v.get("fpVal", 0)
                        results.append({"start_ms": start, "value": val})
        return results
    except Exception as e:
        logger.error(f"Fit API error for {data_type}: {e}")
        return []


def _post_sync_pipeline(user: User, db: Session):
    """After sync: update stress detection, health metrics, re-compute points."""
    from app.services.risk_service import compute_diabetes_risk
    from app.services.lifestyle_points_service import compute_lifestyle_points

    try:
        compute_diabetes_risk(user, db)
    except Exception as e:
        logger.warning(f"Post-sync diabetes risk failed for user {user.id}: {e}")

    try:
        compute_lifestyle_points(user, db)
    except Exception as e:
        logger.warning(f"Post-sync lifestyle points failed for user {user.id}: {e}")
