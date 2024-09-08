from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection import get_db
from app.database.database import Database
from app.services.squarespace_service import SquarespaceService

router = APIRouter(prefix="/order", tags=["Order"])


# order.create
@router.post("/create")
async def on_order_create(request: Request, db: AsyncSession = Depends(get_db)):
    database = Database(session=db)
    service = SquarespaceService(db=database)

    body = await request.json()

    await service.create_subscription(body)


# order.update
@router.post("/update")
async def on_order_update(request: Request, db: AsyncSession = Depends(get_db)):
    database = Database(session=db)
    service = SquarespaceService(db=database)

    body = await request.json()

    await service.update_subscription(body)
