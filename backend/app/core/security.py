import base64
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.errors import DomainError

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_hasher.verify(plain_password, password_hash)


def create_access_token(
    user_id: uuid.UUID, family_id: uuid.UUID | None = None, version: int = 0
) -> tuple[str, int]:
    expires_in = settings.access_token_expires_minutes * 60
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "jti": str(uuid.uuid4()),
        "sid": str(family_id or uuid.uuid4()),
        "ver": version,
    }
    return jwt.encode(
        payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    ), expires_in


def decode_access_token(token: str) -> uuid.UUID:
    return uuid.UUID(decode_access_claims(token)["sub"])


def decode_access_claims(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={
                "require_exp": True,
                "require_iat": True,
                "require_sub": True,
                "require_aud": True,
                "require_iss": True,
                "require_jti": True,
            },
        )
        if payload.get("type") != "access":
            raise JWTError("wrong token type")
        uuid.UUID(payload["sub"])
        uuid.UUID(payload["sid"])
        if not isinstance(payload["ver"], int):
            raise ValueError("invalid version")
        return dict(payload)
    except (JWTError, KeyError, ValueError, TypeError, AttributeError) as exc:
        raise DomainError(
            "invalid_token", "Authentication token is invalid or expired", 401
        ) from exc


def new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    return raw, hash_refresh_token(raw)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def token_cipher() -> Fernet:
    if settings.token_encryption_key:
        return Fernet(settings.token_encryption_key.get_secret_value().encode())
    key = hashlib.sha256(("outbox:" + settings.jwt_secret_key.get_secret_value()).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))
