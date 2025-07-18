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

class UserSupabase:
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

    def dataCreateUser(self, user: UserCreate) -> dict:
        try:
            user_data = user.dict(exclude_unset=True)
            user_data["user_id"] = str(uuid4())
            user_data["password"] = self.hash_password(user_data["password"])
            user_data["secret"] = pyotp.random_base32() if user_data.get("use_2fa") else ""
            user_data["created_at"] = datetime.utcnow().isoformat()
            user_data["updated_at"] = datetime.utcnow().isoformat()
            response = self.supabase.table("users").insert(user_data).execute()
            logger.info(f"Created user with username: {user.username}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Failed to create user {user.username}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

    def dataGetUsers(self) -> List[dict]:
        try:
            response = self.supabase.table("users").select("*").order("created_at", desc=True).execute()
            logger.info(f"Retrieved {len(response.data)} users")
            logger.debug(f"Raw Supabase response: {json.dumps(response.data, indent=2)}")
            users = []
            for item in response.data:
                try:
                    user = UserInDB(**item)
                    users.append(user.dict())
                except Exception as e:
                    logger.error(f"Failed to parse user data {item.get('username', 'unknown')}: {str(e)}")
                    continue
            return users
        except Exception as e:
            logger.error(f"Failed to retrieve users: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")

    def dataGetUser(self, user_id: UUID) -> Optional[dict]:
        try:
            response = self.supabase.table("users").select("*").eq("user_id", str(user_id)).execute()
            logger.debug(f"Raw Supabase response for user_id {user_id}: {json.dumps(response.data, indent=2)}")
            if response.data:
                logger.info(f"Retrieved user with user_id: {user_id}")
                return UserInDB(**response.data[0]).dict()
            logger.info(f"User not found with user_id: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve user: {str(e)}")

    def dataGetUserByUsername(self, username: str) -> Optional[dict]:
        try:
            response = self.supabase.table("users").select("*").eq("username", username).execute()
            logger.debug(f"Raw Supabase response for username {username}: {json.dumps(response.data, indent=2)}")
            if response.data:
                logger.info(f"Retrieved user with username: {username}")
                return UserInDB(**response.data[0]).dict()
            logger.info(f"User not found with username: {username}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve user {username}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve user: {str(e)}")

    def dataUpdateUser(self, user_id: UUID, updates: UserUpdate) -> dict:
        try:
            update_data = updates.dict(exclude_unset=True)
            if "password" in update_data and update_data["password"]:
                update_data["password"] = self.hash_password(update_data["password"])
            if "use_2fa" in update_data and update_data["use_2fa"]:
                update_data["secret"] = pyotp.random_base32()
            elif "use_2fa" in update_data and not update_data["use_2fa"]:
                update_data["secret"] = ""
            update_data["updated_at"] = datetime.utcnow().isoformat()
            response = self.supabase.table("users").update(update_data).eq("user_id", str(user_id)).execute()
            if not response.data:
                logger.info(f"User not found with user_id: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            logger.info(f"Updated user with user_id: {user_id}")
            return response.data[0]
        except HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

    def dataDeleteUser(self, user_id: UUID) -> dict:
        try:
            response = self.supabase.table("users").delete().eq("user_id", str(user_id)).execute()
            if not response.data:
                logger.info(f"User not found with user_id: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            logger.info(f"Deleted user with user_id: {user_id}")
            return response.data[0]
        except HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

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

    def dataSearchUsersByUsername(self, username: str):
        logging.debug(f"[SUPABASE] Searching DB with ilike for username: {username}")
        
        try:
            response = self.supabase.from_("users") \
                .select("*") \
                .ilike("username", f"%{username}%") \
                .execute()

            if response.data:
                logging.debug(f"[SUPABASE] Found {len(response.data)} users")
            else:
                logging.debug("[SUPABASE] No users found")

            return response.data if response.data else []
        
        except Exception as e:
            logging.error(f"[SUPABASE] Error searching users: {e}")
            return []

