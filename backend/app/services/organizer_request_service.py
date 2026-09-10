import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.features import Notification
from app.models.organizer_request import OrganizerRequest
from app.models.user import User, UserRole
from app.schemas.organizer_request import OrganizerRequestCreate, OrganizerRequestReview
from app.services.account_service import locked_user, require_verified
from app.services.notification_service import audit


def list_requests(
    db: Session,
    limit: int,
    offset: int,
    user_id: uuid.UUID | None = None,
    status: str | None = None,
    q: str | None = None,
) -> tuple[list[OrganizerRequest], int]:
    statement = select(OrganizerRequest).join(User, User.id == OrganizerRequest.user_id)
    if user_id:
        statement = statement.where(OrganizerRequest.user_id == user_id)
    if status:
        statement = statement.where(OrganizerRequest.status == status)
    if q:
        statement = statement.where(
            or_(
                User.email.icontains(q, autoescape=True),
                User.name.icontains(q, autoescape=True),
                OrganizerRequest.organization.icontains(q, autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    return list(
        db.scalars(
            statement.order_by(OrganizerRequest.created_at.desc(), OrganizerRequest.id)
            .limit(limit)
            .offset(offset)
        )
    ), total


def submit(db: Session, actor: User, request: OrganizerRequestCreate) -> OrganizerRequest:
    user = locked_user(db, actor.id)
    require_verified(user)
    if user.role != UserRole.ATTENDEE:
        raise ConflictError("already_organizer", "This account already has hosting access")
    if db.scalar(
        select(OrganizerRequest.id).where(
            OrganizerRequest.user_id == user.id, OrganizerRequest.status == "pending"
        )
    ):
        raise ConflictError("application_pending", "An application is already pending")
    row = OrganizerRequest(user_id=user.id, **request.model_dump())
    db.add(row)
    db.commit()
    return row


def resolve(
    db: Session, row: OrganizerRequest, actor: User, status: str, feedback: str | None
) -> None:
    row.status, row.feedback = status, feedback
    row.reviewer_id, row.reviewed_at = actor.id, datetime.now(UTC)
    audit(db, actor, f"organizer_request.{status}", row.id, {"user_id": str(row.user_id)})
    db.add(
        Notification(
            user_id=row.user_id,
            topic=f"organizer_request.{status}",
            message=f"Your organizer application was {status}."
            + (f" {feedback}" if feedback else ""),
        )
    )


def resolve_pending(db: Session, user: User, actor: User) -> None:
    row = db.scalar(
        select(OrganizerRequest)
        .where(OrganizerRequest.user_id == user.id, OrganizerRequest.status == "pending")
        .with_for_update()
    )
    if row:
        resolve(db, row, actor, "approved", "Hosting access granted by an administrator.")


def review(
    db: Session, request_id: uuid.UUID, actor: User, request: OrganizerRequestReview
) -> OrganizerRequest:
    from app.services.user_service import lock_admins

    lock_admins(db)
    user_id = db.scalar(select(OrganizerRequest.user_id).where(OrganizerRequest.id == request_id))
    if not user_id:
        raise NotFoundError("organizer_request")
    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    assert user is not None
    row = db.scalar(
        select(OrganizerRequest)
        .where(OrganizerRequest.id == request_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    assert row is not None
    if row.status != "pending":
        raise ConflictError("already_reviewed", "This application has already been reviewed")
    if request.status == "approved":
        if not user.is_active:
            raise ConflictError("account_inactive", "Reactivate this account before approval")
        if user.role != UserRole.ADMIN:
            user.role = UserRole.ORGANIZER
    resolve(db, row, actor, request.status, request.feedback)
    db.commit()
    return row
