from contextlib import asynccontextmanager

from fastapi import FastAPI
from north_admin import setup_admin

from app.core.admin import admin_app
from app.routers.auth_router import router as user_router
from app.routers.dev_router import router as dev_router
from app.routers.healthcheck_router import router as healthcheck_router
from app.routers.order_router import router as order_router
from app.routers.statement_router import router as statement_router
from app.services.scheduler import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_service.start()
    yield
    scheduler_service.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(dev_router)
app.include_router(healthcheck_router)
app.include_router(order_router)
app.include_router(statement_router)

setup_admin(
    admin_app=admin_app,
    app=app,
)
