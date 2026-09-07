from sqlalchemy.orm import Session

from app.models.outbox import OutboxMessage


def enqueue(db: Session, topic: str, payload: dict[str, object]) -> OutboxMessage:
    message = OutboxMessage(topic=topic, payload=payload)
    db.add(message)
    return message
