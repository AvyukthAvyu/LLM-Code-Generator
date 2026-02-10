from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MessageCreate(BaseModel):
    role: str
    content: str

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    class Config:
        orm_mode = True

class ChatCreate(BaseModel):
    title: Optional[str] = "Untitled chat"

class ChatOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: List[MessageOut] = []
    class Config:
        orm_mode = True

class UserOut(BaseModel):
    id: int
    email: str
    is_admin: bool
    created_at: datetime
    class Config:
        orm_mode = True
