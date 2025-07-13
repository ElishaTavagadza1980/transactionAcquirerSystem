from fastapi import APIRouter, Form, Depends
from app.services.users_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    twofa_code: str = Form(None),
    user_service: UserService = Depends(UserService)
):
    return await user_service.authenticate_user(username, password, twofa_code)