from fastapi import APIRouter, Depends, BackgroundTasks

from app.core.security import get_current_user

from app.db import database
from app.schemas import rsvp
from sqlalchemy.orm import Session
from app.services import rsvp_service
from app.services.email_service import send_rsvp_email


router = APIRouter(
    prefix='/rsvp',
    tags=['Rsvp']
)

@router.post('/')
def rsvp(
    rsvp: rsvp.Rsvp,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: int = Depends(get_current_user)
):
    result = rsvp_service.create_rsvp(db, rsvp, current_user)

    if result.get('send_email') and result.get('email_data'):
        background_tasks.add_task(send_rsvp_email, **result['email_data'])

    return {'msg': result['msg']}