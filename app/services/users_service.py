from fastapi import HTTPException
from uuid import UUID
from app.data_access.users_supabase import UserSupabase
from app.models.users_model import UserCreate, UserUpdate
import logging

class UserService:
    def __init__(self):
        self.supabase = UserSupabase()

    def create_user(self, user_data: dict):
        return self.supabase.dataCreateUser(UserCreate(**user_data))

    def get_users(self):
        return self.supabase.dataGetUsers()

    def get_user(self, user_id: UUID):
        user = self.supabase.dataGetUser(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_user_by_username(self, username: str):
        user = self.supabase.dataGetUserByUsername(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def update_user(self, user_id: UUID, user_data: dict):
        return self.supabase.dataUpdateUser(user_id, UserUpdate(**user_data))

    def delete_user(self, user_id: UUID):
        self.supabase.dataDeleteUser(user_id)
        return {"message": "User deleted successfully"}

    def toggle_user_active(self, user_id: UUID, is_active: bool):
        return self.supabase.dataUpdateUser(user_id, UserUpdate(is_active=is_active))

    def authenticate_user(self, username: str, password: str, twofa_code: str = None):
        return self.supabase.authenticate_user(username, password, twofa_code)
    
    def search_users_by_username(self, username: str):
        logging.debug(f"[SERVICE] Searching users with username like: {username}")
        return self.supabase.dataSearchUsersByUsername(username)

