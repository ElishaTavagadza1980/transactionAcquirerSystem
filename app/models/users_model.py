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


class UserUpdate(BaseModel):  # No longer inherits from UserBase
    username: Optional[str] = None
    password: Optional[str] = None
    use_2fa: Optional[bool] = None
    is_active: Optional[bool] = None
    secret: Optional[str] = None


class UserInDB(UserBase):
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ToggleActiveRequest(BaseModel):
    is_active: bool
