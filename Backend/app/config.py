"""
IndusVision Backend - Configuration
Loads settings from environment variables / .env file.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = next(
    (parent for parent in _CONFIG_DIR.parents if (parent / "Worker-Safety" / "best.pt").is_file()),
    _CONFIG_DIR.parents[1],
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "indusvision"

    # JWT
    JWT_SECRET_KEY: str = "dev_secret_change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Worker safety inference
    PPE_MODEL_PATH: str = str(PROJECT_ROOT / "Worker-Safety" / "best.pt")
    PPE_CONFIDENCE_THRESHOLD: float = 0.5
    LOG_FILE_PATH: str = str(_CONFIG_DIR.parents[0] / "logs" / "indusvision.log")

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL_TO: str = ""


settings = Settings()
