from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://fashionvision_ai_user:fashionvision_ai_pass@localhost:5432/fashionvision_ai"
    DATABASE_URL_SYNC: str = "postgresql://fashionvision_ai_user:fashionvision_ai_pass@localhost:5432/fashionvision_ai"
    SECRET_KEY: str = "dev_secret_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    MEDIA_DIR: str = "/app/media"
    MAX_IMAGE_SIZE_MB: int = 5

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()