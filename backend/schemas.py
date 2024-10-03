from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str
    employee: str


class Token(BaseModel):
    access_token: str
    token_type: str


class Message(BaseModel):
    text: str
    conversation_id: int
    is_user: bool
    timestamp: datetime


class MessageResponse(BaseModel):
    response: str


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    employee_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    title: str
    employee_id: str
