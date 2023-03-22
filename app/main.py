from fastapi import FastAPI, Depends
from typing import List
from . import models, schemas
from .database import engine, SessionLocal
from sqlalchemy.orm import Session


app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

models.Base.metadata.create_all(bind=engine)

@app.get('/')
def test():
    return {'msg': 'I am working fine!!!'}


## Endpoints for Events
@app.get('/events', tags=['Events'])
def get_events(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    return events

@app.post('/add_event', response_model=schemas.Event, tags=['Events'])
def add_event(request: schemas.Event, db: Session = Depends(get_db)):
    new_event = models.Event(event_name = request.event_name, event_details = request.event_details)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event

## API endpoints for user
@app.get('/get_users', response_model=List[schemas.User], tags=['User'])
def get_user(db: Session = Depends(get_db)):
    user = db.query(models.User).all()
    return user

@app.post('/create_user', response_model=schemas.User, tags=['User'])
def create_user(request: schemas.User, db: Session = Depends(get_db)):
    new_user = models.User(name = request.name, email = request.email, password = request.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

