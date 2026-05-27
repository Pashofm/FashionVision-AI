from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://fashionvision_ai_user:fashionvision_ai_pass@localhost:5432/fashionvision_ai"
    DATABASE_URL_SYNC: str = "postgresql://fashionvision_ai_user:fashionvision_ai_pass@localhost:5432/fashionvision_ai"
    SECRET_KEY: str = "dev_secret_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SESSION_TIMEOUT_MINUTES: int = 30
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    MEDIA_DIR: str = "/app/media"
    MAX_IMAGE_SIZE_MB: int = 5
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLIENT_TIMEZONE_HEADER: str = "X-Timezone"
    DEFAULT_TIMEZONE: str = "America/Mazatlan"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = (
            str(ROOT_DIR / ".env.local"),
            str(ROOT_DIR / ".env"),
        )
        case_sensitive = True
        extra = "ignore"


settings = Settings()


def update_session_timeout(minutes: int):
    global settings
    settings.SESSION_TIMEOUT_MINUTES = minutes