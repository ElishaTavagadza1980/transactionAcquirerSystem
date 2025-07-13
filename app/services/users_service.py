from fastapi import HTTPException
from uuid import UUID
from app.data_access.users_supabase import UserSupabase
from app.models.users_model import UserCreate, UserUpdate

class UserService:
    def __init__(self):
        self.supabase = UserSupabase()

    async def create_user(self, user_data: dict):
        return await self.supabase.dataCreateUser(UserCreate(**user_data))

    async def get_users(self):
        return await self.supabase.dataGetUsers()

    async def get_user(self, user_id: UUID):
        user = await self.supabase.dataGetUser(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_user_by_username(self, username: str):
        user = await self.supabase.dataGetUserByUsername(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update_user(self, user_id: UUID, user_data: dict):
        return await self.supabase.dataUpdateUser(user_id, UserUpdate(**user_data))

    async def delete_user(self, user_id: UUID):
        await self.supabase.dataDeleteUser(user_id)
        return {"message": "User deleted successfully"}

    async def toggle_user_active(self, user_id: UUID, is_active: bool):
        return await self.supabase.dataUpdateUser(user_id, UserUpdate(is_active=is_active))

    async def authenticate_user(self, username: str, password: str, twofa_code: str = None):
        return await self.supabase.dataAuthenticateUser(username, password, twofa_code)