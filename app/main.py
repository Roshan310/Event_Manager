from fastapi import FastAPI
from . import models
from .database import engine
from .routers import events, users, auth, rsvps

description = """
Event manager API helps you do awesome stuff. 🚀

## Events

You can create different events.
You can see upcoming events.

## RSVP
You will be able to register for the events.

## Users

You will be able to:

* **Create users** .
* **Read users** .
"""

app = FastAPI(
    title='Event Manager',
    description=description
)


models.Base.metadata.create_all(bind=engine)

app.include_router(events.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(rsvps.router)
