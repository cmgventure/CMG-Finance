from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import UnitOfWorkDep, category_service, get_current_user
from app.enums.base import OrderDirection
from app.schemas.category import Category, CategoryCreateRequest, CategoryUpdateRequest

categories_router = APIRouter(prefix="/categories", tags=["Admin Categories"])


@categories_router.get("")
async def get_categories(
    current_user: get_current_user,
    service: category_service,
    unit_of_work: UnitOfWorkDep,
    page: int = 1,
    page_size: int = 100,
    sort_by: str | None = None,
    sort_order: OrderDirection = OrderDirection.ASC,
    filter_by: str | None = None,
    filter_value: str | None = None,
) -> dict[str, Any]:
    return await service.get_categories(unit_of_work, page, page_size, sort_by, sort_order, filter_by, filter_value)


@categories_router.get("/{category_id}")
async def get_category(
    current_user: get_current_user,
    service: category_service,
    unit_of_work: UnitOfWorkDep,
    category_id: UUID,
) -> Category:
    return await service.get_category(unit_of_work, category_id)


@categories_router.post("")
async def create_category(
    current_user: get_current_user,
    service: category_service,
    unit_of_work: UnitOfWorkDep,
    category: CategoryCreateRequest,
) -> Category:
    return await service.create_category(unit_of_work, category)


@categories_router.patch("/{category_id}")
async def update_category(
    current_user: get_current_user,
    service: category_service,
    unit_of_work: UnitOfWorkDep,
    category_id: UUID,
    category: CategoryUpdateRequest,
) -> Category:
    return await service.update_category(unit_of_work, category_id, category)


@categories_router.delete("/{category_id}")
async def delete_category(
    current_user: get_current_user,
    service: category_service,
    unit_of_work: UnitOfWorkDep,
    category_id: UUID,
) -> dict[str, str]:
    return await service.delete_category(unit_of_work, category_id)
