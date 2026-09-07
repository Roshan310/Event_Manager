import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.token import RefreshToken


def by_hash(db: Session, token_hash: str, *, for_update: bool = False) -> RefreshToken | None:
    statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def revoke_family(db: Session, family_id: uuid.UUID, revoked_at: object) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=revoked_at)
    )
