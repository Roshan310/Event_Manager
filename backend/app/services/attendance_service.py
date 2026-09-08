import csv
import hashlib
import hmac
import io
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import qrcode  # type: ignore[import-untyped]
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.time import as_utc
from app.models.event import Event, EventStatus
from app.models.registration import Registration, RegistrationStatus
from app.models.user import User
from app.services.event_service import _can_manage
from app.services.notification_service import audit


def managed(db: Session, event_id: uuid.UUID, actor: User) -> Event:
    event = db.scalar(select(Event).where(Event.id == event_id).with_for_update())
    if not event:
        raise NotFoundError("event")
    if not _can_manage(actor, event):
        raise ForbiddenError()
    return event


def ticket_token(row: Registration) -> str:
    digest = hmac.new(
        settings.jwt_secret_key.get_secret_value().encode(),
        f"ticket:{row.id}:{row.ticket_nonce}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{row.id}.{digest}"


def ticket(db: Session, event_id: uuid.UUID, actor: User) -> dict[str, Any]:
    event = db.scalar(select(Event).where(Event.id == event_id).with_for_update())
    row = db.scalar(
        select(Registration).where(
            Registration.event_id == event_id, Registration.attendee_id == actor.id
        )
    )
    if not event or not row:
        raise NotFoundError("registration")
    if row.status != RegistrationStatus.CONFIRMED or event.status != EventStatus.PUBLISHED:
        raise ConflictError("ticket_unavailable", "A confirmed registration is required")
    if as_utc(event.ends_at) <= datetime.now(UTC):
        raise ConflictError("ticket_expired", "This event has ended")
    if row.ticket_nonce is None:
        row.ticket_nonce = secrets.token_urlsafe(32)
        db.commit()
    return {
        "registration_id": row.id,
        "event_id": event_id,
        "event_title": event.title,
        "attendee_name": actor.name,
        "qr_payload": ticket_token(row),
        "qr_url": f"{settings.public_base_url}/api/v1/events/{event_id}/registrations/me/ticket/qr",
        "checked_in_at": row.checked_in_at,
    }


def qr_png(payload: str) -> bytes:
    buffer = io.BytesIO()
    qrcode.make(payload).save(buffer, format="PNG")
    return buffer.getvalue()


def check_window(event: Event) -> None:
    now = datetime.now(UTC)
    if event.status != EventStatus.PUBLISHED or not (
        as_utc(event.starts_at) - timedelta(hours=1) <= now < as_utc(event.ends_at)
    ):
        raise ConflictError(
            "check_in_closed", "Check-in opens one hour before start and closes at end"
        )


def check_in(
    db: Session,
    event_id: uuid.UUID,
    actor: User,
    registration_id: uuid.UUID | None = None,
    token: str | None = None,
) -> Registration:
    event = managed(db, event_id, actor)
    check_window(event)
    if token:
        try:
            registration_id = uuid.UUID(token.split(".")[0])
        except ValueError as exc:
            raise ConflictError("invalid_ticket", "Ticket is invalid") from exc
    row = db.get(Registration, registration_id)
    if not row or row.event_id != event_id:
        raise NotFoundError("registration")
    if token and (not row.ticket_nonce or not hmac.compare_digest(ticket_token(row), token)):
        raise ConflictError("invalid_ticket", "Ticket is invalid")
    if row.status != RegistrationStatus.CONFIRMED or not row.attendee.is_active:
        raise ConflictError("check_in_ineligible", "Only active confirmed attendees can check in")
    if not row.checked_in_at:
        row.checked_in_at, row.checked_in_by = datetime.now(UTC), actor.id
        audit(db, actor, "registration.checked_in", row.id)
    db.commit()
    return row


def undo(
    db: Session, event_id: uuid.UUID, registration_id: uuid.UUID, actor: User, reason: str
) -> None:
    event = managed(db, event_id, actor)
    check_window(event)
    row = db.get(Registration, registration_id)
    if not row or row.event_id != event_id:
        raise NotFoundError("registration")
    if row.checked_in_at:
        row.checked_in_at, row.checked_in_by = None, None
        audit(db, actor, "registration.check_in_undone", row.id, {"reason": reason})
    db.commit()


def summary(db: Session, event_id: uuid.UUID, actor: User) -> dict[str, Any]:
    event = managed(db, event_id, actor)
    counts: dict[RegistrationStatus, int] = dict(
        db.execute(
            select(Registration.status, func.count())
            .where(Registration.event_id == event_id)
            .group_by(Registration.status)
        )
        .tuples()
        .all()
    )
    confirmed = counts.get(RegistrationStatus.CONFIRMED, 0)
    checked_in = (
        db.scalar(
            select(func.count())
            .select_from(Registration)
            .where(
                Registration.event_id == event_id,
                Registration.checked_in_at.is_not(None),
                Registration.status == RegistrationStatus.CONFIRMED,
            )
        )
        or 0
    )
    return {
        "event_id": event_id,
        "confirmed": confirmed,
        "waitlisted": counts.get(RegistrationStatus.WAITLISTED, 0),
        "cancelled": counts.get(RegistrationStatus.CANCELLED, 0),
        "checked_in": checked_in,
        "remaining_seats": max(0, event.capacity - confirmed),
        "attendance_rate": round(checked_in / confirmed, 4) if confirmed else 0.0,
    }


def roster_csv(db: Session, event_id: uuid.UUID, actor: User) -> str:
    managed(db, event_id, actor)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["registration_id", "name", "email", "status", "checked_in_at"])
    rows = db.scalars(
        select(Registration)
        .options(joinedload(Registration.attendee))
        .where(Registration.event_id == event_id)
        .order_by(Registration.created_at, Registration.id)
    )

    def safe(value: str) -> str:
        return (
            "'" + value
            if value.lstrip().startswith(("=", "+", "-", "@"))
            or value.startswith(("\t", "\r", "\n"))
            else value
        )

    for row in rows:
        writer.writerow(
            [
                str(row.id),
                safe(row.attendee.name),
                safe(row.attendee.email),
                row.status.value,
                row.checked_in_at.isoformat() if row.checked_in_at else "",
            ]
        )
    return buffer.getvalue()
