"""Google Fit integration: OAuth flow + data sync."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.google_fit_service import get_oauth_url, exchange_code, sync_data

router = APIRouter(prefix="/fit", tags=["Google Fit"])


@router.get("/connect")
def connect():
    """Return Google OAuth2 authorization URL."""
    return {"auth_url": get_oauth_url()}


@router.get("/callback")
async def callback(
    code: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle OAuth2 callback, exchange code for tokens."""
    try:
        result = await exchange_code(code, user, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
async def sync(
    days: int = Query(1, ge=1, le=7),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync fitness data from Google Fit."""
    try:
        result = await sync_data(user, db, days)
        return {"message": "Sync complete", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
def status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Check if Google Fit is connected."""
    from app.models.user import FitOAuthToken
    token = db.query(FitOAuthToken).filter(FitOAuthToken.user_id == user.id).first()
    if not token:
        return {"connected": False}
    return {
        "connected": True,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
    }
