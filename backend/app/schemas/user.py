from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str

class UserProfile(UserBase):
    id: int
    spotify_connected: bool
    preferences: Dict[str, Any]

class Token(BaseModel):
    access_token: str
    token_type: str
