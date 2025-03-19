from fastapi import APIRouter

from app.api.dependencies import auth_service, get_current_user
from app.schemas.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me")
async def get_user(current_user: get_current_user) -> User:
    return current_user


@router.get("/status")
async def get_user_status(current_user: get_current_user) -> bool:
    return current_user.superuser or bool(current_user.subscription)


@router.get("/google")
async def get_google_access_token(current_user: get_current_user, service: auth_service) -> str:
    return await service.get_google_access_token(current_user)
