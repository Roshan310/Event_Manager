from fastapi import FastAPI, Depends, HTTPException, status
from typing import List, Annotated
from . import models, schemas
from .database import engine, get_db
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .hashing import Hashing
from .authenticate import create_access_token, create_refresh_token

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


models.Base.metadata.create_all(bind=engine)


@app.get('/items')
def items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {'token': token}

## Endpoints for Events
@app.get('/events', tags=['Events'])
def get_events(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    return events

@app.post('/add_event', response_model=schemas.Event, tags=['Events'])
def add_event(request: schemas.Event, db: Session = Depends(get_db)):
    new_event = models.Event(event_name = request.event_name, event_details = request.event_details, user_id = 2)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event

## API endpoints for user
@app.get('/get_users', response_model=List[schemas.User], tags=['User'])
def get_user(db: Session = Depends(get_db)):
    user = db.query(models.User).all()
    return user

@app.post('/sign_up', response_model=schemas.User, tags=['User'])
def create_user(request: schemas.User, db: Session = Depends(get_db)):

    new_user = models.User(name = request.name, email = request.email, password = Hashing.hash(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == form_data.username).first()
    if user is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect username')
    elif not Hashing.verify_password(form_data.password, user.password):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect username or password')

    return {'access_token': create_access_token(user.email),
            'refresh_token': create_refresh_token(user.email)}
