import os
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt

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

    to_encode = {'exp': expires_delta, 'sub': str(subject)}
    jwt_encoded = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

    return jwt_encoded

def create_refresh_token(subject: Union[str, Any], expires_delta: int = None):
    if expires_delta is not None:
        expires_delta = datetime.utcnow()  + expires_delta

    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRES_MINUTES)

    to_encode = {'exp': expires_delta, 'sub': str(subject)}
    jwt_encoded = jwt.encode(to_encode, JWT_REFRESH_KEY, algorithm=ALGORITHM)

    return jwt_encoded