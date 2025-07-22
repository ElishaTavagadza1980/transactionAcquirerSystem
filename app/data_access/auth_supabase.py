from supabase import create_client, Client
from app.models.users_model import UserCreate, UserInDB, UserUpdate
from starlette.config import Config
from typing import List, Optional
from fastapi import HTTPException
import logging
import json
import pyotp
import hashlib
from uuid import UUID, uuid4
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthSupabase:
    def __init__(self):
        try:
            config = Config(".env")
            db_url: str = config("SUPABASE_URL")
            db_key: str = config("SUPABASE_KEY")
            self.supabase: Client = create_client(db_url, db_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.hash_password(password) == hashed_password

    def verify_2fa(self, secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code) 
  

    def authenticate_user(self, username: str, password: str) -> dict | None:
        try:
            response = self.supabase.table("users").select("*").eq("username", username).execute()
            logger.info(f"Supabase query response for username {username}: {response}")

            if not response.data or len(response.data) == 0:
                logger.info(f"No user found with username: {username}")
                return None

            user = response.data[0]

            if not self.verify_password(password, user.get("password")):
                logger.info(f"Invalid password for username: {username}")
                return None

            logger.info(f"Authenticated user with username: {username}")

            # ✅ Return full user data required for login checks
            return {
                "id": user.get("user_id"),
                "username": user.get("username"),
                "is_active": user.get("is_active"),
                "use_2fa": user.get("use_2fa"),
                "secret": user.get("secret"),
            }
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {str(e)}")
            return None


