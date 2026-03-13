import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(_BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "FitGenix"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./fitgenix.db"
    FERNET_KEY: str = ""
    CALORIENINJAS_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:3000"
    TIMEZONE: str = "Asia/Kolkata"

    @property
    def base_dir(self) -> Path:
        return _BASE_DIR

    @property
    def ml_root(self) -> Path:
        return _BASE_DIR.parent / "ml"

    @property
    def ml_models_dir(self) -> Path:
        return self.ml_root / "saved_models"

    @property
    def ml_data_dir(self) -> Path:
        return self.ml_root / "data" / "processed"

    @property
    def data_dir(self) -> Path:
        return _BASE_DIR / "data"

    @property
    def knowledge_base_dir(self) -> Path:
        return self.data_dir / "knowledge_base"

    @property
    def is_demo(self) -> bool:
        return self.ENVIRONMENT == "demo"


settings = Settings()
