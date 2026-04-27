from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from ...db import database
from app.models.user import User as user_model
from app.schemas.user import UserCreate, UserOut
from app.schemas.pagination import PaginatedResponse
from app.core.security import get_current_user
from app.services import user_service

router = APIRouter(
    prefix='/users',
    tags=['Users']
)

@router.get('/')
def get_user(
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    db: Session = Depends(database.get_db)
):
    users, total = user_service.get_all_users(db, limit, offset)
    return PaginatedResponse.create(items=users, total=total, limit=limit, offset=offset)

@router.get('/me', response_model=UserOut)
def get_current_user(user: user_model = Depends(get_current_user)):
    return user

@router.post('/', response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(database.get_db)):
    return user_service.create_user(db, user)