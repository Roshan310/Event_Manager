from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db import database
from app.models.user import User
from app.core.security import Hashing


router = APIRouter()


@router.post('/login')
def login(user_credential: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(User).filter(User.email == user_credential.username).first()
    print(user)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect username')
    elif not Hashing.verify_password(user_credential.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect username or password')

    return {'access_token': create_access_token(user.id)}