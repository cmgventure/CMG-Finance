from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.admin.auth import auth_router
from app.routers.admin.categories import categories_router
from app.routers.auth_router import router as user_router
from app.routers.dev_router import router as dev_router
from app.routers.fmp_routers import router as fmp_router
from app.routers.healthcheck_router import router as healthcheck_router
from app.routers.order_router import router as order_router
from app.routers.statement_router import router as statement_router
from app.services.scheduler import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_service.start()
    yield
    scheduler_service.shutdown()


origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://admin.cmgfinances.com",
]

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/admin")
app.include_router(categories_router, prefix="/admin")
app.include_router(fmp_router, prefix="/fmp")
app.include_router(user_router)
app.include_router(dev_router)
app.include_router(healthcheck_router)
app.include_router(order_router)
app.include_router(statement_router)
