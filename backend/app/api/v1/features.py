import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import admin_user, current_user, event_manager
from app.core.throttle import throttle
from app.db.database import get_db
from app.models.user import User
from app.schemas.event import EventOut
from app.schemas.features import (
    Acknowledgement,
    AuditOut,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    ChangePassword,
    CheckInRequest,
    EmailRequest,
    EventSummary,
    NotificationOut,
    NotificationRead,
    OutboxOut,
    Preferences,
    ProfileUpdate,
    ResetPassword,
    StatusUpdate,
    TicketOut,
    TokenRequest,
    TransferOwner,
    WorkerStatus,
)
from app.schemas.pagination import PaginatedResponse
from app.schemas.registration import RegistrationOut
from app.schemas.user import UserOut
from app.services import account_service as accounts
from app.services import attendance_service as attendance
from app.services import features_service as service
from app.services import media_service as media
from app.services import registration_service, user_service

router = APIRouter(tags=["Extended workflows"])
DB = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(current_user)]
Admin = Annotated[User, Depends(admin_user)]
Manager = Annotated[User, Depends(event_manager)]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]
Reason = Annotated[str, Query(min_length=3, max_length=500)]


@router.patch("/users/me", response_model=UserOut)
def profile(request: ProfileUpdate, db: DB, actor: Actor) -> User:
    return accounts.update_profile(db, actor, request.name)


@router.post(
    "/auth/forgot-password",
    response_model=Acknowledgement,
    status_code=202,
    dependencies=[Depends(throttle("recovery"))],
)
def forgot(request: EmailRequest, db: DB) -> Acknowledgement:
    accounts.request_token(db, str(request.email), "reset")
    return Acknowledgement()


@router.post("/auth/reset-password", status_code=204, dependencies=[Depends(throttle("recovery"))])
def reset(request: ResetPassword, db: DB) -> Response:
    accounts.consume_token(db, request.token, "reset", request.password)
    return Response(status_code=204)


@router.post(
    "/auth/verification/request",
    response_model=Acknowledgement,
    status_code=202,
    dependencies=[Depends(throttle("verification"))],
)
def verification_request(request: EmailRequest, db: DB) -> Acknowledgement:
    accounts.request_token(db, str(request.email), "verify")
    return Acknowledgement()


@router.post(
    "/auth/verification/confirm", status_code=204, dependencies=[Depends(throttle("verification"))]
)
def verification_confirm(request: TokenRequest, db: DB) -> Response:
    accounts.consume_token(db, request.token, "verify")
    return Response(status_code=204)


@router.post("/auth/change-password", status_code=204, dependencies=[Depends(throttle("password"))])
def password(request: ChangePassword, db: DB, actor: Actor) -> Response:
    accounts.change_password(db, actor, request.current_password, request.password)
    return Response(status_code=204)


@router.post("/auth/logout-all", status_code=204)
def logout_all(db: DB, actor: Actor) -> Response:
    accounts.logout_all(db, actor)
    return Response(status_code=204)


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: DB) -> object:
    return service.categories(db)


@router.get("/admin/categories", response_model=list[CategoryOut])
def all_categories(db: DB, actor: Admin) -> object:
    return service.categories(db, True)


@router.post("/admin/categories", response_model=CategoryOut, status_code=201)
def create_category(request: CategoryCreate, db: DB, actor: Admin) -> object:
    return service.save_category(db, request.name, actor)


@router.patch("/admin/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: uuid.UUID, request: CategoryUpdate, db: DB, actor: Admin
) -> object:
    return service.save_category(db, request.name, actor, category_id, request.is_active)


@router.get("/users/me/bookmarks", response_model=PaginatedResponse[EventOut])
def bookmarks(db: DB, actor: Actor, limit: Limit = 20, offset: Offset = 0) -> object:
    rows, total = service.bookmarks(db, actor, limit, offset)
    return PaginatedResponse.create(
        [EventOut.model_validate(r) for r in rows], total, limit, offset
    )


@router.put("/users/me/bookmarks/{event_id}", status_code=204)
def add_bookmark(event_id: uuid.UUID, db: DB, actor: Actor) -> Response:
    service.bookmark(db, event_id, actor)
    return Response(status_code=204)


@router.delete("/users/me/bookmarks/{event_id}", status_code=204)
def remove_bookmark(event_id: uuid.UUID, db: DB, actor: Actor) -> Response:
    service.bookmark(db, event_id, actor, True)
    return Response(status_code=204)


@router.get("/users/me/notifications", response_model=PaginatedResponse[NotificationOut])
def notifications(
    db: DB, actor: Actor, limit: Limit = 20, offset: Offset = 0, unread_only: bool = False
) -> object:
    rows, total = service.notifications(db, actor, limit, offset, unread_only)
    return PaginatedResponse.create(
        [NotificationOut.model_validate(r) for r in rows], total, limit, offset
    )


@router.patch("/users/me/notifications/{notification_id}", response_model=NotificationOut)
def notification_read(
    notification_id: uuid.UUID, request: NotificationRead, db: DB, actor: Actor
) -> object:
    return service.read_notification(db, actor, notification_id)


@router.post("/users/me/notifications/read-all", status_code=204)
def read_all(db: DB, actor: Actor) -> Response:
    service.read_all(db, actor)
    return Response(status_code=204)


@router.get("/users/me/notification-preferences", response_model=Preferences)
def preferences(db: DB, actor: Actor) -> object:
    return service.preferences(db, actor)


@router.patch("/users/me/notification-preferences", response_model=Preferences)
def update_preferences(request: Preferences, db: DB, actor: Actor) -> object:
    return service.preferences(db, actor, request.reminder_emails)


@router.patch("/admin/users/{user_id}/status", response_model=UserOut)
def user_status(user_id: uuid.UUID, request: StatusUpdate, db: DB, actor: Admin) -> object:
    return user_service.change_status(db, user_id, request.is_active, actor)


@router.patch("/admin/events/{event_id}/organizer", response_model=EventOut)
def transfer(event_id: uuid.UUID, request: TransferOwner, db: DB, actor: Admin) -> object:
    return service.transfer(db, event_id, request.organizer_id, actor)


@router.get("/admin/audit-logs", response_model=PaginatedResponse[AuditOut])
def audit_logs(
    db: DB, actor: Admin, limit: Limit = 20, offset: Offset = 0, target_id: uuid.UUID | None = None
) -> object:
    rows, total = service.audit_logs(db, limit, offset, target_id)
    return PaginatedResponse.create(
        [AuditOut.model_validate(r) for r in rows], total, limit, offset
    )


@router.get("/admin/outbox", response_model=PaginatedResponse[OutboxOut])
def outbox(
    db: DB, actor: Admin, limit: Limit = 20, offset: Offset = 0, failed_only: bool = False
) -> object:
    rows, total = service.outbox(db, limit, offset, failed_only)
    return PaginatedResponse.create(
        [OutboxOut.model_validate(r) for r in rows], total, limit, offset
    )


@router.post("/admin/outbox/{message_id}/retry", response_model=OutboxOut)
def retry(message_id: uuid.UUID, db: DB, actor: Admin) -> object:
    return service.retry(db, message_id, actor)


@router.get("/admin/worker-status", response_model=WorkerStatus)
def worker(db: DB, actor: Admin) -> object:
    return service.worker_status(db)


@router.get("/events/{event_id}/registrations/me", response_model=RegistrationOut)
def registration(event_id: uuid.UUID, db: DB, actor: Actor) -> object:
    return registration_service.mine_for_event(db, event_id, actor)


@router.delete("/events/{event_id}/registrations/{registration_id}", status_code=204)
def remove_registration(
    event_id: uuid.UUID, registration_id: uuid.UUID, db: DB, actor: Manager, reason: Reason
) -> Response:
    registration_service.remove(db, event_id, registration_id, actor, reason)
    return Response(status_code=204)


@router.get("/events/{event_id}/registrations/me/ticket", response_model=TicketOut)
def ticket(event_id: uuid.UUID, db: DB, actor: Actor) -> object:
    return attendance.ticket(db, event_id, actor)


@router.get(
    "/events/{event_id}/registrations/me/ticket/qr",
    response_class=Response,
    responses={200: {"content": {"image/png": {"schema": {"type": "string", "format": "binary"}}}}},
)
def ticket_qr(event_id: uuid.UUID, db: DB, actor: Actor) -> Response:
    result = attendance.ticket(db, event_id, actor)
    return Response(attendance.qr_png(result["qr_payload"]), media_type="image/png")


@router.post("/events/{event_id}/check-ins", response_model=RegistrationOut)
def check_in(event_id: uuid.UUID, request: CheckInRequest, db: DB, actor: Manager) -> object:
    return attendance.check_in(db, event_id, actor, request.registration_id, request.token)


@router.delete("/events/{event_id}/check-ins/{registration_id}", status_code=204)
def undo_check_in(
    event_id: uuid.UUID, registration_id: uuid.UUID, db: DB, actor: Manager, reason: Reason
) -> Response:
    attendance.undo(db, event_id, registration_id, actor, reason)
    return Response(status_code=204)


@router.get("/organizer/events/{event_id}/summary", response_model=EventSummary)
def summary(event_id: uuid.UUID, db: DB, actor: Manager) -> object:
    return attendance.summary(db, event_id, actor)


@router.get(
    "/events/{event_id}/registrations/export",
    response_class=Response,
    responses={200: {"content": {"text/csv": {"schema": {"type": "string"}}}}},
)
def export(event_id: uuid.UUID, db: DB, actor: Manager) -> Response:
    return Response(
        attendance.roster_csv(db, event_id, actor),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="roster-{event_id}.csv"'},
    )


@router.put(
    "/events/{event_id}/cover", response_model=EventOut, dependencies=[Depends(throttle("upload"))]
)
def upload_cover(event_id: uuid.UUID, file: UploadFile, db: DB, actor: Manager) -> object:
    return media.cover(db, event_id, actor, file.file.read(media.MAX_BYTES + 1))


@router.delete("/events/{event_id}/cover", response_model=EventOut)
def delete_cover(event_id: uuid.UUID, db: DB, actor: Manager) -> object:
    return media.cover(db, event_id, actor, None)


@router.get(
    "/events/{event_id}/cover",
    response_class=FileResponse,
    responses={
        200: {"content": {"image/jpeg": {"schema": {"type": "string", "format": "binary"}}}}
    },
)
def public_cover(event_id: uuid.UUID, db: DB) -> FileResponse:
    return FileResponse(media.cover_path(db, event_id), media_type="image/jpeg")


@router.get(
    "/organizer/events/{event_id}/cover",
    response_class=FileResponse,
    responses={
        200: {"content": {"image/jpeg": {"schema": {"type": "string", "format": "binary"}}}}
    },
)
def private_cover(event_id: uuid.UUID, db: DB, actor: Manager) -> FileResponse:
    return FileResponse(media.cover_path(db, event_id, actor), media_type="image/jpeg")


@router.get(
    "/events/{event_id}/calendar.ics",
    response_class=Response,
    responses={200: {"content": {"text/calendar": {"schema": {"type": "string"}}}}},
)
def calendar(event_id: uuid.UUID, db: DB) -> Response:
    return Response(
        media.calendar(db, event_id),
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="event-{event_id}.ics"'},
    )
