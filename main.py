import asyncio

from fastapi import FastAPI
from hypercorn.asyncio import serve

from app.core.config import hypercorn_config
from app.routers.auth_router import router as user_router
from app.routers.dev_router import router as dev_router
from app.routers.healthcheck_router import router as healthcheck_router
from app.routers.order_router import router as order_router
from app.routers.statement_router import router as statement_router

app = FastAPI()

app.include_router(user_router)
app.include_router(dev_router)
app.include_router(healthcheck_router)
app.include_router(order_router)
app.include_router(statement_router)

