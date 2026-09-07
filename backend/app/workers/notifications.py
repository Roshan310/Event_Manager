import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.outbox import OutboxMessage
from app.services.email_service import send_notification

logger = logging.getLogger(__name__)


def process_batch() -> int:
    with SessionLocal() as db:
        messages = list(
            db.scalars(
                select(OutboxMessage)
                .where(
                    OutboxMessage.processed_at.is_(None),
                    OutboxMessage.failed_at.is_(None),
                    OutboxMessage.available_at <= datetime.now(UTC),
                )
                .order_by(OutboxMessage.created_at)
                .with_for_update(skip_locked=True)
                .limit(settings.notification_batch_size)
            )
        )
        for message in messages:
            try:
                send_notification(message.topic, message.payload)
                message.processed_at = datetime.now(UTC)
            except Exception as exc:
                message.attempts += 1
                message.last_error = str(exc)[:2000]
                if message.attempts >= settings.notification_max_attempts:
                    message.failed_at = datetime.now(UTC)
                else:
                    message.available_at = datetime.now(UTC) + timedelta(
                        seconds=min(2**message.attempts * 30, 3600)
                    )
                logger.exception(
                    "Notification delivery failed", extra={"outbox_id": str(message.id)}
                )
        db.commit()
        return len(messages)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("Notification worker started")
    while True:
        if process_batch() == 0:
            time.sleep(settings.notification_poll_seconds)


if __name__ == "__main__":
    main()
