import hashlib
import time
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import Depends, Request
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import DomainError
from app.db.database import get_db
from app.models.features import RateBucket


def throttle(kind: str) -> Callable[..., None]:
    def dependency(request: Request, db: Session = Depends(get_db)) -> None:
        address = request.client.host if request.client else "unknown"
        if address in settings.trusted_proxy_ips:
            # The configured proxy must overwrite this header, not append untrusted input.
            address = request.headers.get("x-forwarded-for", address).split(",")[0].strip()
        window = settings.rate_window_seconds
        bucket = int(time.time()) // window
        key = hashlib.sha256(f"{kind}:{address}:{bucket}".encode()).hexdigest()
        expires = datetime.fromtimestamp((bucket + 1) * window, UTC)
        statement = insert(RateBucket).values(key=key, count=1, expires_at=expires)
        upsert = statement.on_conflict_do_update(
            index_elements=[RateBucket.key], set_={"count": RateBucket.count + 1}
        ).returning(RateBucket.count)
        count = db.scalar(upsert) or 1
        db.commit()
        maximum = settings.upload_rate_limit if kind == "upload" else settings.auth_rate_limit
        if count > maximum:
            raise DomainError(
                "rate_limited",
                "Too many requests",
                429,
                {"retry_after": max(1, int(expires.timestamp() - time.time()))},
            )

    return dependency
