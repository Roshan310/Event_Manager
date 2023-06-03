from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt, JWTError
from . import schemas, models, database
from sqlalchemy.orm import Session

oauth_scheme = OAuth2PasswordBearer('login')

ACCESS_TOKEN_EXPIRES_MINUTES = 30 #30 Minutes
REFRESH_TOKEN_EXPIRES_MINUTES = 60 * 24 * 7 #7 days
ALGORITHM = "HS256"
JWT_SECRET_KEY = 'ABCDEFGH123'
JWT_REFRESH_KEY = 'ABCDEFGH23'

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
        if id is None:
            print("No id")
        token_data = schemas.TokenData(id=id)

    except JWTError:
        raise credential_exception

    return token_data

def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(database.get_db)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate',
                                         headers={"WWW-Authenticate": "Bearer"})
    token_data = verify_access_token(token, credential_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    return user