import re
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, func, or_, select

from app.core.config import settings
from app.core.time import as_utc
from app.db.database import SessionLocal
from app.models.event import Event
from app.models.features import ActionToken, AuditLog, Notification, RateBucket
from app.models.outbox import OutboxMessage
from app.models.token import RefreshToken


def cleanup(apply: bool = False) -> dict[str, int]:
    now = datetime.now(UTC)
    counts: dict[str, int] = {}
    rules = [
        (ActionToken, ActionToken.expires_at < now - timedelta(days=7)),
        # Keep revoked ancestors until expiry so refresh reuse remains detectable.
        (RefreshToken, RefreshToken.expires_at < now - timedelta(days=7)),
        (RateBucket, RateBucket.expires_at < now),
        (Notification, Notification.read_at < now - timedelta(days=90)),
        (AuditLog, AuditLog.created_at < now - timedelta(days=365)),
        (
            OutboxMessage,
            or_(
                OutboxMessage.processed_at < now - timedelta(days=30),
                OutboxMessage.failed_at < now - timedelta(days=90),
            ),
        ),
    ]
    with SessionLocal() as db:
        expired_payloads = 0
        for message in db.scalars(
            select(OutboxMessage)
            .where(
                OutboxMessage.topic.startswith("account."),
                OutboxMessage.processed_at.is_(None),
                OutboxMessage.failed_at.is_(None),
                or_(OutboxMessage.lease_until.is_(None), OutboxMessage.lease_until < now),
            )
            .with_for_update(skip_locked=True)
        ):
            action_id = message.payload.get("action_id")
            action = db.get(ActionToken, uuid.UUID(str(action_id))) if action_id else None
            if action is None or action.used_at or as_utc(action.expires_at) <= now:
                expired_payloads += 1
                if apply:
                    message.payload = {}
                    message.processed_at = now
                    message.claim_id, message.lease_until = None, None
        counts["expired_security_payloads"] = expired_payloads
        for model, condition in rules:
            counts[model.__tablename__] = (
                db.scalar(select(func.count()).select_from(model).where(condition)) or 0
            )
            if apply:
                db.execute(delete(model).where(condition))
        referenced = set(
            db.scalars(select(Event.cover_filename).where(Event.cover_filename.is_not(None)))
        )
        root = Path(settings.media_root)
        orphans = [
            p
            for p in root.glob("*.jpg")
            if p.name not in referenced
            and re.fullmatch(r"[0-9a-f]{32}\.jpg", p.name)
            and p.is_file()
            and not p.is_symlink()
            and p.stat().st_mtime < (now - timedelta(days=1)).timestamp()
        ]
        counts["orphaned_covers"] = len(orphans)
        if apply:
            db.commit()
            for path in orphans:
                path.unlink()
    return counts
