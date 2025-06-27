from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...db import database
from app.models.user import User as user_model
from app.schemas.user import UserCreate, UserOut
from app.core.security import get_current_user
from app.services import user_service

router = APIRouter(
    prefix='/users',
    tags=['Users']
)

@router.get('/', response_model=List[UserOut])
def get_user(db: Session = Depends(database.get_db)):
    user = db.query(user_model).all()
    return user

@router.get('/me', response_model=UserOut)
def get_current_user(user: user_model = Depends(get_current_user)):
    return user

@router.post('/', response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(database.get_db)):
    return user_service.create_user(db, user)