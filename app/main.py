from fastapi import FastAPI
from . import models
from .database import engine
from .routers import events, users, auth, rsvps

app = FastAPI()


models.Base.metadata.create_all(bind=engine)

app.include_router(events.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(rsvps.router)
