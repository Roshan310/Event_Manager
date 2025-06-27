from fastapi import FastAPI

from app.api.v1 import event, rsvp, user, auth
from .db.database import engine
from app.db import database
from fastapi.middleware.cors import CORSMiddleware

description = """
Event manager API helps you do awesome stuff. 🚀

## Events

You can create different events.
You can see upcoming events.

## RSVP
You will be able to register for the events.

## Users

You will be able to:

* **Create users** 
* **Read users** 
"""

app = FastAPI(
    title='Event Manager',
    description=description,
    contact = {
        'email': 'yuvrajaryal83@gmail.com'
    }
)


app.add_middleware(
    CORSMiddleware,
    allow_origins= ["*"],  # Allows all origins, you can specify a list of allowed origins instead
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database.Base.metadata.create_all(bind=engine)

app.include_router(event.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(rsvp.router)
