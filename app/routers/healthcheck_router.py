from fastapi import APIRouter

router = APIRouter(tags=["Healthcheck"])


@router.get("/healthcheck")
async def healthcheck():
    return "OK"
