from fastapi import APIRouter

router = APIRouter(tags=["Healthcheck"])


@router.get("/healthcheck")
async def healthcheck() -> str:
    return "OK"
