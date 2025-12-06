from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProjectCreate(BaseModel):
    name: str

class ProjectOut(BaseModel):
    id: int
    name: str
    class Config:
        orm_mode = True

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = None
    remind_before_minutes: Optional[int] = None
    project_id: Optional[int] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    date: Optional[datetime]
    remind_before_minutes: Optional[int]
    completed: bool
    project_id: Optional[int]
    class Config:
        orm_mode = True

class NLPRequest(BaseModel):
    text: str
