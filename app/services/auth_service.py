from uuid import UUID
from app.data_access.users_supabase import AuthSupabase
from app.models.users_model import UserUpdate

class AuthService:
    def __init__(self):
        self.supabase = AuthSupabase()    

    def toggle_user_active(self, user_id: UUID, is_active: bool):
        return self.supabase.dataUpdateUser(user_id, UserUpdate(is_active=is_active))

    def authenticate_user(self, username: str, password: str, twofa_code: str = None):
        return self.supabase.authenticate_user(username, password, twofa_code)
    


