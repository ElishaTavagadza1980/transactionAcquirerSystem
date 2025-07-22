from fastapi import APIRouter, HTTPException, Form, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from app.config import session_store, SESSION_COOKIE_NAME, SESSION_EXPIRATION_SECONDS
from app.data_access.auth_supabase import AuthSupabase
import secrets
import time
import logging
import pyotp

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/view_templates") 

router = APIRouter()
logger = logging.getLogger(__name__)
auth_supabase = AuthSupabase()

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    twofa_code: str = Form(default=None)
):
    try:
        logger.debug(f"🔍 Received login request: username={username}, twofa_code={twofa_code}")

        user = auth_supabase.authenticate_user(username, password)
        logger.debug(f"👤 authenticate_user() returned: {user}")

        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password.")

        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="User account is inactive.")

        if user.get("use_2fa", False):
            if not twofa_code:
                raise HTTPException(status_code=401, detail="2FA code is required.")

            secret = user.get("secret", "")
            if not secret:
                raise HTTPException(status_code=500, detail="2FA configuration error.")

            totp = pyotp.TOTP(secret)
            if not totp.verify(twofa_code, valid_window=1):
                raise HTTPException(status_code=401, detail="Invalid 2FA code.")

        # ✅ Passed all checks, create session
        session_id = secrets.token_hex(16)
        session_store[session_id] = {
            "user_id": user["id"],
            "username": user["username"],
            "expires_at": time.time() + SESSION_EXPIRATION_SECONDS
        }
        logger.info(f"✅ Session created for user {username}: {session_id}")

        response = RedirectResponse(url="/home", status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=SESSION_EXPIRATION_SECONDS
        )
        return response

    except HTTPException as e:
        # 👇 Re-render login page with error message
        logger.warning(f"❌ Login failed: {e.detail}")
        return templates.TemplateResponse(
            "auth/login.html",  # Your login template
            {"request": request, "error_message": e.detail, "username": username},
            status_code=e.status_code
        )
@router.get("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id and session_id in session_store:
        del session_store[session_id]
        response.delete_cookie(SESSION_COOKIE_NAME)
    return RedirectResponse(url="/", status_code=303)




