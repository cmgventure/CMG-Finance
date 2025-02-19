from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints.admin.auth import auth_router
from app.api.endpoints.admin.categories import categories_router
from app.api.endpoints.auth import router as user_router
from app.api.endpoints.dev import router as dev_router
from app.api.endpoints.fmp import router as fmp_router
from app.api.endpoints.healthcheck import router as healthcheck_router
from app.api.endpoints.order import router as order_router

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://admin.cmgfinances.com",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/admin")
app.include_router(categories_router, prefix="/admin")
app.include_router(fmp_router)
app.include_router(user_router)
app.include_router(dev_router)
app.include_router(healthcheck_router)
app.include_router(order_router)
# app.include_router(statement_router)
