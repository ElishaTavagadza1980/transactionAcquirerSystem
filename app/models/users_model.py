from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    use_2fa: bool = False
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    secret: Optional[str] = None

class UserUpdate(UserBase):
    password: Optional[str] = None
    secret: Optional[str] = None

class UserInDB(UserBase):
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True