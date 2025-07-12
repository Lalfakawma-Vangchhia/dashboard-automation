from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # Database - PostgreSQL configuration
    database_url: str = os.getenv("DATABASE_URL")
    
    # PostgreSQL specific settings
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "automation_dashboard")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD")

    # JWT Authentication
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_token_expire_minutes: int = 440 

    # Facebook Integration
    facebook_app_id: str | None = os.getenv("FACEBOOK_APP_ID")
    facebook_app_secret: str | None = os.getenv("FACEBOOK_APP_SECRET")

    # Instagram Integration
    instagram_app_id: str | None = os.getenv("INSTAGRAM_APP_ID")
    instagram_app_secret: str | None = os.getenv("INSTAGRAM_APP_SECRET")

    # Groq AI Integration
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")

    # Stability AI Integration
    stability_api_key: str | None = os.getenv("STABILITY_API_KEY")

    # IMGBB Integration
    imgbb_api_key: str | None = os.getenv("IMGBB_API_KEY")

    # Cloudinary Integration
    cloudinary_cloud_name: str | None = os.getenv("CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str | None = os.getenv("CLOUDINARY_API_KEY")
    cloudinary_api_secret: str | None = os.getenv("CLOUDINARY_API_SECRET")
    cloudinary_upload_preset: str | None = os.getenv("CLOUDINARY_UPLOAD_PRESET")

    # Google Drive Integration
    google_drive_client_id: str | None = os.getenv("GOOGLE_DRIVE_CLIENT_ID")
    google_drive_client_secret: str | None = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET")
    google_drive_redirect_uri: str | None = os.getenv("GOOGLE_DRIVE_REDIRECT_URI")
    google_drive_access_token: str | None = os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN")
    google_drive_refresh_token: str | None = os.getenv("GOOGLE_DRIVE_REFRESH_TOKEN")

    # Backend base URL for OAuth callbacks
    backend_base_url: str = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"

    # CORS
    cors_origins: List[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
