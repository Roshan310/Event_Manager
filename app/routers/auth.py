from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, database, oauth2
from ..hashing import Hashing


router = APIRouter()


@router.post('/login')
def login(user_credential: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_credential.username).first()
    
    if user is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect username')
    elif not Hashing.verify_password(user_credential.password, user.password):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect username or password')

    return {'access_token': oauth2.create_access_token(user.id)}