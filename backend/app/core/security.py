from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt, JWTError
from app.db import database
from app.schemas import tokendata as token_schemas
from app.models import user as user_model
from sqlalchemy.orm import Session
from .config import settings


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class Hashing:

    def hash(password: str):
        return pwd_context.hash(password)

    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
    

oauth_scheme = OAuth2PasswordBearer('login')

ACCESS_TOKEN_EXPIRES_MINUTES = settings.access_token_expires_minutes 
ALGORITHM = settings.algorithm
JWT_SECRET_KEY = settings. jwt_secret_key

def create_access_token(subject: Union[str, Any], expires_delta: int = None):
    if expires_delta is not None:
        expires_delta = datetime.utcnow()  + expires_delta

    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)

    to_encode = {'exp': expires_delta, 'id': str(subject)}
    jwt_encoded = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

    return jwt_encoded

def verify_access_token(token: str, credential_exception):
    try:
        print("Payload incoming")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        id = payload.get('id')
        print(f"ID: {id}")
        if id is None:
            print("No id")
        token_data = token_schemas.TokenData(id=id)

    except JWTError:
        raise credential_exception

    return token_data

def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(database.get_db)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate',
                                         headers={"WWW-Authenticate": "Bearer"})
    token_data = verify_access_token(token, credential_exception)
    user = db.query(user_model.User).filter(user_model.User.id == token_data.id).first()
    return user

