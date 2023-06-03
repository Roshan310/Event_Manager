from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database
from ..hashing import Hashing

router = APIRouter(
    prefix='/users',
    tags=['Users']
)

@router.get('/', response_model=List[schemas.UserOut])
def get_user(db: Session = Depends(database.get_db)):
    user = db.query(models.User).all()
    return user

@router.post('/', response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    user.password = Hashing.hash(user.password)
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user