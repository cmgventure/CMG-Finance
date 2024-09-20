from fastapi import FastAPI

from app.routers.auth_router import router as user_router
from app.routers.dev_router import router as dev_router
from app.routers.healthcheck_router import router as healthcheck_router
from app.routers.order_router import router as order_router
from app.routers.statement_router import router as statement_router
from app.services.scheduler import scheduler_service

app = FastAPI()

app.include_router(user_router)
app.include_router(dev_router)
app.include_router(healthcheck_router)
app.include_router(order_router)
app.include_router(statement_router)

@app.on_event("startup")
async def startup():
    scheduler_service.start()

@app.on_event("shutdown")
async def startup():
    scheduler_service.shutdown()
