from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Event(Base):

    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, unique=True, index=True)
    event_details = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_by = relationship('User')