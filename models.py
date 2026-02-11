from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class Vacancy(Base):
    __tablename__ = 'vacancy'
    
    id = Column(Integer, primary_key=True, index=True)
    hh_id = Column(String, unique=True, index=True)
    name = Column(String)
    url = Column(String)
    description = Column(Text, nullable=True)
    
class Resume(Base):
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)