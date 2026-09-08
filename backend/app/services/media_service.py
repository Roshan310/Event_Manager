import io
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, DomainError, NotFoundError
from app.core.time import as_utc, utc_now
from app.models.event import EventStatus
from app.models.user import User
from app.services import attendance_service, event_service

MAX_BYTES = 5 * 1024 * 1024


def cover(db: Session, event_id: uuid.UUID, actor: User, data: bytes | None) -> dict[str, object]:
    event = attendance_service.managed(db, event_id, actor)
    if event.status == EventStatus.CANCELLED or (
        event.status == EventStatus.PUBLISHED and as_utc(event.starts_at) <= utc_now()
    ):
        raise ConflictError("event_not_editable", "Cover cannot be changed for this event")
    if data is None:
        event.cover_filename = None
    else:
        if len(data) > MAX_BYTES:
            raise DomainError("image_too_large", "Cover must be at most 5 MiB", 413)
        try:
            with Image.open(io.BytesIO(data), formats=["JPEG", "PNG", "WEBP"]) as source:
                if source.width * source.height > 20_000_000:
                    raise DomainError("image_too_large", "Cover must be at most 20 megapixels", 413)
                source.load()
                clean = Image.new("RGB", source.size, "white")
                converted = source.convert("RGBA")
                clean.paste(converted, mask=converted.getchannel("A"))
                root = Path(settings.media_root)
                root.mkdir(parents=True, exist_ok=True)
                filename = f"{uuid.uuid4().hex}.jpg"
                clean.save(root / filename, "JPEG", quality=85)
                event.cover_filename = filename
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise DomainError(
                "invalid_image", "Upload a valid JPEG, PNG, or WebP image", 422
            ) from exc
    db.commit()
    return event_service.serialize(db, event)


def cover_path(db: Session, event_id: uuid.UUID, actor: User | None = None) -> Path:
    from app.models.event import Event

    event = db.get(Event, event_id)
    if (
        not event
        or (
            event.status == EventStatus.DRAFT
            and (actor is None or not event_service._can_manage(actor, event))
        )
        or not event.cover_filename
    ):
        raise NotFoundError("cover")
    path = Path(settings.media_root) / event.cover_filename
    if not path.is_file():
        raise NotFoundError("cover")
    return path


def calendar(db: Session, event_id: uuid.UUID) -> str:
    event = event_service.public_get(db, event_id)

    def escape(value: object) -> str:
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\n", "\\n")
            .replace(";", "\\;")
            .replace(",", "\\,")
        )

    from datetime import datetime

    def date(value: object) -> str:
        assert isinstance(value, datetime)
        return as_utc(value).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Event Manager//EN",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{event_id}@event-manager",
        f"SEQUENCE:{event['revision']}",
        f"DTSTAMP:{date(event['updated_at'])}",
        f"DTSTART:{date(event['starts_at'])}",
        f"DTEND:{date(event['ends_at'])}",
        f"SUMMARY:{escape(event['title'])}",
        f"DESCRIPTION:{escape(event['description'])}",
        f"LOCATION:{escape(event['location'])}",
        "STATUS:" + ("CANCELLED" if event["status"] == "cancelled" else "CONFIRMED"),
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    # Fold by UTF-8 octets without splitting a character (RFC 5545).
    folded: list[str] = []
    for line in lines:
        current = ""
        for char in line:
            if len((current + char).encode()) > 75:
                folded.append(current)
                current = " "
            current += char
        folded.append(current)
    return "\r\n".join(folded) + "\r\n"
