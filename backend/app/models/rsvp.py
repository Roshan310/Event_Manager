from sqlalchemy import Column, Integer, ForeignKey
from app.db.database import Base

class Rsvp(Base):

    __tablename__ = 'rsvps'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_id = Column(Integer, ForeignKey('events.id'))