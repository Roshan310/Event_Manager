from sqlalchemy.orm import Session
from app.models.user import User

def add_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_all_users(db: Session, limit: int = 10, offset: int = 0):
    """Get all users with pagination"""
    query = db.query(User)
    total = query.count()
    users = query.offset(offset).limit(limit).all()
    return users, total