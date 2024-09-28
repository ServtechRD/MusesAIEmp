from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    date_joined = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime)

    images = relationship('Image', back_populates='owner')
    messages = relationship('Conversation', back_populates='owner')

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    image_path = Column(String(255))
    description = Column(Text)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship('User', back_populates='images')

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship('User', back_populates='messages')
