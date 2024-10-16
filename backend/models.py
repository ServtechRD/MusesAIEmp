from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, PrimaryKeyConstraint
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


class ImageFileVersion(Base):
    __tablename__ = 'image_file_versions'

    user_name = Column(String(50), nullable=False)
    filename = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    version = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('user_name', 'filename', 'version'),
    )

    def __repr__(self):
        return f"<ImageFileVersion(user_id={self.user_name}, filename={self.filename}, version={self.version}, timestamp={self.timestamp})>"

class AppFunctionVersion(Base):
    __tablename__ = 'app_function_versions'

    user_name = Column(String(50), nullable=False)
    proj_id = Column(String(100), nullable=False)
    app_name = Column(String(100), nullable=False)
    func_name = Column(String(200), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    version = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('user_name', 'proj_id', 'app_name', 'func_name', 'version'),
    )

    def __repr__(self):
        return f"<AppFunctionVersion(user_id={self.user_name}, proj_id={self.proj_id}, app_name={self.app_name}, func_name={self.func_name}, version={self.version}, timestamp={self.timestamp})>"