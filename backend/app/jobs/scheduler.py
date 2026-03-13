"""APScheduler background jobs for periodic tasks."""
import logging
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _nightly_recompute():
    """Recompute lifestyle points and leaderboard for all active users (runs at 23:55 IST)."""
    from app.database import SessionLocal
    from app.models.user import User
    from app.services.lifestyle_points_service import force_recompute
    from app.services.leaderboard_service import update_leaderboard

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active.is_(True)).all()
        logger.info(f"Nightly recompute: {len(users)} users")
        for user in users:
            try:
                force_recompute(user, db, date.today())
                update_leaderboard(user, db)
            except Exception as e:
                logger.error(f"Nightly job failed for user {user.id}: {e}")
    finally:
        db.close()


def _weekly_risk_refresh():
    """Refresh diabetes and CVD risk scores weekly (Sunday 02:00 IST)."""
    from app.database import SessionLocal
    from app.models.user import User
    from app.services.risk_service import compute_diabetes_risk, compute_cvd_risk

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active.is_(True)).all()
        logger.info(f"Weekly risk refresh: {len(users)} users")
        for user in users:
            try:
                compute_diabetes_risk(user, db)
                compute_cvd_risk(user, db)
            except Exception as e:
                logger.error(f"Risk refresh failed for user {user.id}: {e}")
    finally:
        db.close()


def start_scheduler():
    """Register all scheduled jobs and start the scheduler."""
    # Nightly at 23:55 IST (18:25 UTC)
    scheduler.add_job(
        _nightly_recompute,
        CronTrigger(hour=18, minute=25),
        id="nightly_recompute",
        replace_existing=True,
    )

    # Weekly Sunday 02:00 IST (Saturday 20:30 UTC)
    scheduler.add_job(
        _weekly_risk_refresh,
        CronTrigger(day_of_week="sat", hour=20, minute=30),
        id="weekly_risk_refresh",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("APScheduler started with 2 jobs")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
