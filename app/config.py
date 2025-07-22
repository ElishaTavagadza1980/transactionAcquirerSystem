import secrets
import time

# Session Management Configuration
SECRET_KEY = secrets.token_hex(32) 
SESSION_COOKIE_NAME = "my_app_session_id"
SESSION_EXPIRATION_SECONDS = 3600  # 1 hour


session_store = {}
