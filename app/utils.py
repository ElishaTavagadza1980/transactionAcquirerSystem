# app/utils.py

from fastapi import Request
from app.config import session_store, SESSION_COOKIE_NAME
import time

async def get_current_user(request: Request):
    print("🔍 get_current_user: Entered")

    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    print(f"🔍 Session ID from cookie: {session_id}")

    if not session_id:
        print("⛔ No session_id in cookie")
        return None

    if session_id not in session_store:
        print("⛔ Session ID not in session_store")
        return None

    session_data = session_store[session_id]
    print(f"🔍 Session data: {session_data}")

    if time.time() > session_data.get("expires_at", 0):
        print("⛔ Session expired")
        del session_store[session_id]
        return None

    user = {
        "user_id": session_data["user_id"],
        "username": session_data.get("username")
    }

    print(f"✅ Returning user: {user}")
    return user
