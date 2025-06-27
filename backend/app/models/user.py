from sqlalchemy import Column, Integer, String
from app.db.database import Base

class User(Base):

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    password = Column(String, index=True, nullable=False)