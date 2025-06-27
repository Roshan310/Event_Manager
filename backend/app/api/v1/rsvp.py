from fastapi import APIRouter, Depends

from app.core.security import get_current_user

from app.db import database
from app.schemas import rsvp
from sqlalchemy.orm import Session
from app.services import rsvp_service


router = APIRouter(
    prefix='/rsvp',
    tags=['Rsvp']
)

@router.post('/')
def rsvp(rsvp: rsvp.Rsvp, db: Session = Depends(database.get_db), current_user: int = Depends(get_current_user)):
    return rsvp_service.create_rsvp(db, rsvp, current_user.id)