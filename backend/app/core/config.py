from functools import lru_cache
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
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
    notification_lease_seconds: int = Field(default=120, ge=30, le=600)
    media_root: str = "media"
    public_base_url: str = "http://localhost:8000"
    token_encryption_key: SecretStr | None = None
    auth_rate_limit: int = Field(default=20, ge=1)
    upload_rate_limit: int = Field(default=10, ge=1)
    rate_window_seconds: int = Field(default=300, ge=1)
    trusted_proxy_ips: list[str] = []

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return value.replace("postgresql://", "postgresql+psycopg://", 1)

    @field_validator("token_encryption_key")
    @classmethod
    def valid_encryption_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value:
            Fernet(value.get_secret_value().encode())
        return value

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, value: list[str]) -> list[str]:
        if any(
            origin == "*" or urlsplit(origin).scheme not in {"http", "https"} for origin in value
        ):
            raise ValueError("CORS origins must be explicit HTTP(S) origins")
        return value

    @field_validator("public_base_url")
    @classmethod
    def valid_public_url(cls, value: str) -> str:
        parts = urlsplit(value)
        if (
            parts.scheme not in {"http", "https"}
            or not parts.netloc
            or parts.query
            or parts.fragment
        ):
            raise ValueError("PUBLIC_BASE_URL must be an HTTP(S) base URL")
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
