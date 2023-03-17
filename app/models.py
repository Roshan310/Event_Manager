from sqlalchemy import Column, Integer, String
from .database import Base

class Event(Base):

    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, unique=True, index=True)
    event_details = Column(String, nullable=False)
    