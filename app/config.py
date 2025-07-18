import secrets
import time

# Session Management Configuration
SECRET_KEY = secrets.token_hex(32)  # Use a strong, securely generated key
SESSION_COOKIE_NAME = "my_app_session_id"
SESSION_EXPIRATION_SECONDS = 3600  # 1 hour

# In-memory store for demonstration. Use Redis/DB for production!
# Structure: {session_id: {"user_id": ..., "username": ..., "expires_at": ...}}
session_store = {}

# Supabase Configuration (loaded from .env in users_supabase.py)
# SUPABASE_URL = "https://kxniyrjofdjzdjpwwvfz.supabase.co"
# SUPABASE_KEY = "your-supabase-anon-key"