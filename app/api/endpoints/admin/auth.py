from fastapi import APIRouter

from app.api.dependencies import UnitOfWorkDep, auth_service
from app.schemas.user import UserLoginRequest

# Authentication router
auth_router = APIRouter(prefix="/auth", tags=["Admin Auth"])


@auth_router.post("/login")
async def get_access_token(
    service: auth_service, unit_of_work: UnitOfWorkDep, credentials: UserLoginRequest
) -> dict[str, str]:
    return await service.get_access_token(unit_of_work, credentials)


@auth_router.post("/token/refresh")
async def refresh_access_token(service: auth_service, refresh_token: str) -> dict[str, str]:
    return await service.refresh_access_token(refresh_token)
