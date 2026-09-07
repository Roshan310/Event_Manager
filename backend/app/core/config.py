from functools import lru_cache

from pydantic import EmailStr, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Event Manager API"
    environment: str = "development"
    database_url: str
    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "event-manager"
    jwt_audience: str = "event-manager-api"
    access_token_expires_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_expires_days: int = Field(default=30, ge=1, le=90)
    cors_origins: list[str] = ["http://localhost:3000"]
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_from_email: EmailStr = "no-reply@example.com"
    smtp_use_tls: bool = False
    notification_batch_size: int = Field(default=20, ge=1, le=100)
    notification_poll_seconds: float = Field(default=2.0, ge=0.1, le=60)
    notification_max_attempts: int = Field(default=5, ge=1, le=20)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
