from fastapi import APIRouter, Request

from app.api.dependencies import UnitOfWorkDep, squarespace_service

router = APIRouter(prefix="/order", tags=["Order"])


# order.create
@router.post("/create")
async def on_order_create(unit_of_work: UnitOfWorkDep, service: squarespace_service, request: Request):
    body = await request.json()
    await service.create_subscription(unit_of_work, body)


# order.update
@router.post("/update")
async def on_order_update(unit_of_work: UnitOfWorkDep, service: squarespace_service, request: Request):
    body = await request.json()
    await service.update_subscription(unit_of_work, body)
