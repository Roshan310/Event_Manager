from fastapi import FastAPI, Depends
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

@app.get('/', tags=['test'])
def test():
    return {'msg': 'I am working fine!!!'}

@app.get('/events')
def get_events(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    return events

@app.post('/add_event', response_model=schemas.Event)
def add_event(request: schemas.Event, db: Session = Depends(get_db)):
    new_event = models.Event(event_name = request.event_name, event_details = request.event_details)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event

