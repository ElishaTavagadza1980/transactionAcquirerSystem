from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from uuid import UUID
from app.users_service import UserService
from app.users_model import UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="app/view_templates")

@router.get("/", response_class=HTMLResponse)
async def get_users(request: Request, user_service: UserService = Depends(UserService)):
    users = await user_service.get_users()
    return templates.TemplateResponse("users.html", {"request": request, "users": users})

@router.post("/add")
async def add_user(user: UserCreate, user_service: UserService = Depends(UserService)):
    return await user_service.create_user(user.dict())

@router.get("/{user_id}")
async def get_user(user_id: UUID, user_service: UserService = Depends(UserService)):
    return await user_service.get_user(user_id)

@router.put("/{user_id}")
async def update_user(user_id: UUID, user: UserUpdate, user_service: UserService = Depends(UserService)):
    return await user_service.update_user(user_id, user.dict(exclude_unset=True))

@router.delete("/{user_id}")
async def delete_user(user_id: UUID, user_service: UserService = Depends(UserService)):
    return await user_service.delete_user(user_id)

@router.patch("/{user_id}/toggle")
async def toggle_user_active(user_id: UUID, data: dict, user_service: UserService = Depends(UserService)):
    return await user_service.toggle_user_active(user_id, data["is_active"])