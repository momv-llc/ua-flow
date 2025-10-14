from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    class Config:
        from_attributes = True

class DocCreate(BaseModel):
    title: str
    content_md: Optional[str] = ""

class DocOut(BaseModel):
    id: int
    title: str
    content_md: Optional[str] = ""
    class Config:
        from_attributes = True
