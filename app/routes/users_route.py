from fastapi import APIRouter, Form, Depends, Request, Response, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from app.services.users_service import UserService
from uuid import uuid4, UUID
import time
from app.config import session_store, SESSION_COOKIE_NAME, SESSION_EXPIRATION_SECONDS
from app.models.users_model import UserCreate, UserUpdate
from fastapi.templating import Jinja2Templates
import logging
from app.models.users_model import ToggleActiveRequest
from fastapi import Query

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

router = APIRouter()
templates = Jinja2Templates(directory="app/view_templates")

@router.get("/", response_class=HTMLResponse)
def get_users_page(request: Request, user_service: UserService = Depends(UserService)):
    users = user_service.get_users()
    return templates.TemplateResponse("users/users.html", {"request": request, "users": users}) 

@router.get("/list", response_class=HTMLResponse)
def get_users_list_page(request: Request, user_service: UserService = Depends(UserService)):
    users = user_service.get_users()
    return templates.TemplateResponse("users/partials/users_list.html", {"request": request, "users": users})

@router.get("/update/{user_id}", response_class=HTMLResponse)
def get_user_update_page(request: Request, user_id: UUID, user_service: UserService = Depends(UserService)):
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("users/partials/users_update.html", {"request": request, "user": user})

@router.get("/edit/{user_id}", response_class=HTMLResponse)
def get_user_edit_page(request: Request, user_id: UUID, user_service: UserService = Depends(UserService)):
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("users/partials/users_edit.html", {"request": request, "user": user})

@router.get("/tr/{user_id}", response_class=HTMLResponse)
def get_user_tr(request: Request, user_id: UUID, user_service: UserService = Depends(UserService)):
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("users/partials/users_tr.html", {"request": request, "user": user})

@router.get("/search", response_class=HTMLResponse)
def search_users(
    request: Request,
    username: str = Query("", alias="username"),  # ✅ explicitly declare query param
    user_service: UserService = Depends(UserService)
):
    logging.info(f"[ROUTE] Search requested for username: '{username}'")

    if username:
        users = user_service.search_users_by_username(username)
        logging.info(f"[ROUTE] Found {len(users)} users matching '{username}'")
    else:
        users = user_service.get_users()
        logging.info("[ROUTE] No username provided, returning all users")

    return templates.TemplateResponse("users/partials/users_tr.html", {
        "request": request,
        "users": users
    })


@router.post("/add")
def add_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    use_2fa: bool = Form(False),
    user_service: UserService = Depends(UserService)
):
    user_data = {"username": username, "password": password, "use_2fa": use_2fa}

    # Actually create the user
    user_service.create_user(user_data)

    # Then fetch updated list
    users = user_service.get_users()

    # Return updated users table rows
    return templates.TemplateResponse("users/partials/users_tr.html", {"request": request, "users": users})

  
@router.get("/{user_id}")
def get_user(user_id: UUID, user_service: UserService = Depends(UserService)):
    return user_service.get_user(user_id)

@router.put("/{user_id}")
def update_user(user_id: UUID, user_data: UserUpdate, user_service: UserService = Depends(UserService)):
    try:
        user_service.update_user(user_id, user_data.dict(exclude_unset=True))
        return {"message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}")
def delete_user(user_id: UUID, user_service: UserService = Depends(UserService)):
    return user_service.delete_user(user_id)


@router.patch("/{user_id}/toggle")
def toggle_user_active(user_id: UUID, payload: ToggleActiveRequest, user_service: UserService = Depends(UserService)):
    try:
        return user_service.toggle_user_active(user_id, payload.is_active)
    except Exception as e:
        logging.exception("Error toggling user active status")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/login")
def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    twofa_code: str = Form(None),
    user_service: UserService = Depends(UserService)
):
    result = user_service.authenticate_user(username, password, twofa_code)
    if result.get("success"):
        session_id = str(uuid4())
        session_data = {
            "user_id": str(result["user"]["user_id"]),
            "expires_at": time.time() + SESSION_EXPIRATION_SECONDS
        }
        session_store[session_id] = session_data
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=SESSION_EXPIRATION_SECONDS
        )
        return RedirectResponse(url="/", status_code=303)  # Redirect to home page on success
    return result

@router.get("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id and session_id in session_store:
        del session_store[session_id]
        response.delete_cookie(SESSION_COOKIE_NAME)
    return RedirectResponse(url="/login", status_code=303)









