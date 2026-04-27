
from sqlalchemy.orm import Session
from app.db.repository import user as user_repo
from app.models import user as user_model
from app.schemas import user as user_schema
from app.core.security import Hashing

def create_user(db: Session, user: user_schema.UserCreate):
    hashed_password = Hashing.hash(user.password)
    new_user = user_model.User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role
    )
    user_repo.add_user(db, new_user)
    return new_user

def get_all_users(db: Session, limit: int = 10, offset: int = 0):
    """Get all users with pagination"""
    return user_repo.get_all_users(db, limit, offset)