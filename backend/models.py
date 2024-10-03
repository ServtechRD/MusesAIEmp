from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
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
    conversations = relationship('Conversation', back_populates='owner')


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
    employee_id = Column(String(25))  # 員工編號
    title = Column(Text)  # 可選：為每個對話添加一個標題
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship('User', back_populates='conversations')

    messages = relationship('Message', back_populates='owner')


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    message = Column(Text)
    response = Column(Text)
    #is_user = Column(Boolean, default=True)  # True if user message, False if AI response
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship('Conversation', back_populates='messages')
