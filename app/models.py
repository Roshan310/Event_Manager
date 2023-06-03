from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Event(Base):

    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, unique=True, index=True)
    event_details = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_by = relationship('User')
    

class User(Base):

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    password = Column(String, index=True, nullable=False)

class Rsvp(Base):

    __tablename__ = 'rsvps'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('events.id'))

                
