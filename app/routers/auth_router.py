from fastapi import APIRouter, Depends

from app.schemas.schemas import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me")
async def get_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/status")
async def get_user_status(current_user: User = Depends(get_current_user)):
    return current_user.superuser or bool(current_user.subscription)
