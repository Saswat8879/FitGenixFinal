"""FitGenix FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import engine, Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _normalize_legacy_profile_values() -> None:
    """Map historical enum strings to current allowed values."""
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE profiles
            SET goal = CASE CAST(goal AS TEXT)
                WHEN 'weight_loss' THEN 'lose_weight'
                WHEN 'muscle_gain' THEN 'gain_muscle'
                WHEN 'diabetes_management' THEN 'manage_condition'
                ELSE CAST(goal AS TEXT)
            END
            WHERE CAST(goal AS TEXT) IN ('weight_loss', 'muscle_gain', 'diabetes_management')
        """))
        conn.execute(text("""
            UPDATE profiles
            SET coaching_style = CASE CAST(coaching_style AS TEXT)
                WHEN 'balanced' THEN 'moderate'
                WHEN 'aggressive' THEN 'intense'
                ELSE CAST(coaching_style AS TEXT)
            END
            WHERE CAST(coaching_style AS TEXT) IN ('balanced', 'aggressive')
        """))
        conn.execute(text("""
            UPDATE profiles
            SET activity_level = CASE CAST(activity_level AS TEXT)
                WHEN 'moderate' THEN 'moderately_active'
                ELSE CAST(activity_level AS TEXT)
            END
            WHERE CAST(activity_level AS TEXT) IN ('moderate')
        """))
        conn.execute(text("""
            UPDATE profiles
            SET work_style = CASE CAST(work_style AS TEXT)
                WHEN 'office' THEN 'desk_job'
                WHEN 'field' THEN 'field_work'
                WHEN 'manual_labor' THEN 'field_work'
                ELSE CAST(work_style AS TEXT)
            END
            WHERE CAST(work_style AS TEXT) IN ('office', 'field', 'manual_labor')
        """))
        conn.execute(text("""
            UPDATE profiles
            SET diet_type = CASE CAST(diet_type AS TEXT)
                WHEN 'standard' THEN 'non_vegetarian'
                WHEN 'balanced' THEN 'non_vegetarian'
                ELSE CAST(diet_type AS TEXT)
            END
            WHERE CAST(diet_type AS TEXT) IN ('standard', 'balanced')
        """))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, load ML models, start scheduler."""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    _normalize_legacy_profile_values()
    logger.info("Database tables created")

    # Load ML models
    from app.services.ml_models import ml_models
    try:
        ml_models.load_all()
    except Exception as e:
        logger.error(f"ML model loading failed: {e}. Endpoints requiring ML will fail.")

    # Start background scheduler
    from app.jobs.scheduler import start_scheduler, stop_scheduler
    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-driven fitness & lifestyle disease management API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.auth import router as auth_router
from app.api.onboarding import router as onboarding_router
from app.api.profile import router as profile_router
from app.api.dashboard import router as dashboard_router
from app.api.plans import router as plans_router
from app.api.logs import router as logs_router
from app.api.lifestyle import router as lifestyle_router
from app.api.health import router as health_router
from app.api.progress import router as progress_router
from app.api.lifestyle_points import router as lp_router
from app.api.fit import router as fit_router
from app.api.chat import router as chat_router
from app.api.community import router as community_router
from app.api.simulate import router as simulate_router
from app.api.admin import router as admin_router

app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(profile_router)
app.include_router(dashboard_router)
app.include_router(plans_router)
app.include_router(logs_router)
app.include_router(lifestyle_router)
app.include_router(health_router)
app.include_router(progress_router)
app.include_router(lp_router)
app.include_router(fit_router)
app.include_router(chat_router)
app.include_router(community_router)
app.include_router(simulate_router)
app.include_router(admin_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Root"])
def health_check():
    from app.services.ml_models import ml_models
    return {
        "status": "healthy",
        "ml_loaded": ml_models.is_loaded,
        "database": "sqlite",
    }
