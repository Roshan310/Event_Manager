from sqlalchemy.orm import Session
import app.db.repository.event as event_repo
from app.models import event as model_event
from app.models import user as user_model
from app.schemas import event as event_schemas


ROLE_ADMIN = 'admin'
ROLE_ORGANIZER = 'organizer'


def _can_manage_event(actor: user_model.User, owner_id: int) -> bool:
    if actor.role == ROLE_ADMIN:
        return True
    if actor.role == ROLE_ORGANIZER and actor.id == owner_id:
        return True
    return False


def create_event(db: Session, event: event_schemas.EventCreate, actor: user_model.User):
    if actor.role not in {ROLE_ADMIN, ROLE_ORGANIZER}:
        return None, 'forbidden'

    new_event = model_event.Event(
        event_name=event.event_name,
        event_details=event.event_details,
        user_id=actor.id
    )
    return event_repo.create_event(db, new_event), None


def list_events(db: Session, limit: int = 10, offset: int = 0):
    return event_repo.get_all_events(db, limit, offset)


def my_events(db: Session, user_id: int, limit: int = 10, offset: int = 0):
    return event_repo.get_user_events(db, user_id, limit, offset)


def get_event_by_id(db: Session, event_id: int):
    return event_repo.get_event_by_id(db, event_id)


def update_event(db: Session, event_id: int, actor: user_model.User, request: event_schemas.EventUpdate):
    event = event_repo.get_event_by_id(db, event_id)
    if not event:
        return None, 'not_found'

    if not _can_manage_event(actor, event.user_id):
        return None, 'forbidden'

    if request.event_name is None and request.event_details is None:
        return None, 'empty_payload'

    if request.event_name is not None:
        event.event_name = request.event_name

    if request.event_details is not None:
        event.event_details = request.event_details

    updated_event = event_repo.update_event(db, event)
    return updated_event, None


def delete_event(db: Session, event_id: int, actor: user_model.User):
    event = event_repo.get_event_by_id(db, event_id)
    if not event:
        return 'not_found'

    if not _can_manage_event(actor, event.user_id):
        return 'forbidden'

    event_repo.delete_event(db, event)
    return None


def total_events(db: Session):
    return event_repo.count_total_events(db)


def my_registered_events(db: Session, user_id: int, limit: int = 10, offset: int = 0):
    return event_repo.get_my_registered_events(db, user_id, limit, offset)