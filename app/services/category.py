from typing import Any
from uuid import UUID

from fastapi import HTTPException

from app.enums.base import OrderDirection
from app.schemas.category import Category, CategoryCreateRequest, CategoryUpdateRequest
from app.utils.unitofwork import ABCUnitOfWork


class CategoryService:
    @staticmethod
    async def get_categories(
        unit_of_work: ABCUnitOfWork,
        page: int = 1,
        page_size: int = 100,
        sort_by: str | None = None,
        sort_order: OrderDirection = OrderDirection.ASC,
        filter_by: str | None = None,
        filter_value: str | None = None,
    ) -> dict[str, Any]:
        # set the offset to start from
        offset = (page - 1) * page_size

        async with unit_of_work:
            # get the categories records from the database
            filters = {filter_by: filter_value} if filter_by and filter_value else {}
            categories = await unit_of_work.category.get_multi(
                offset=offset, order_by=sort_by, order_direction=sort_order, **filters
            )
            # get the total count of categories
            total = await unit_of_work.category.get_count()

        return {"items": categories, "total": total}

    @staticmethod
    async def get_category(
        unit_of_work: ABCUnitOfWork,
        category_id: UUID,
    ) -> Category:
        async with unit_of_work:
            category = await unit_of_work.category.get_one_or_none(id=category_id)

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        return Category.model_validate(category.__dict__)

    @staticmethod
    async def create_category(
        unit_of_work: ABCUnitOfWork,
        category: CategoryCreateRequest,
    ) -> Category:
        async with unit_of_work:
            category = await unit_of_work.category.create(category)

        return Category.model_validate(category.__dict__)

    @staticmethod
    async def update_category(
        unit_of_work: ABCUnitOfWork,
        category_id: UUID,
        category: CategoryUpdateRequest,
    ) -> Category:
        async with unit_of_work:
            db_category = await unit_of_work.category.update(
                category.model_dump(exclude_unset=True), return_object=True, id=category_id
            )

        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")

        return Category.model_validate(db_category.__dict__)

    @staticmethod
    async def delete_category(unit_of_work: ABCUnitOfWork, category_id: UUID) -> dict[str, str]:
        async with unit_of_work:
            db_category = await unit_of_work.category.delete(return_object=True, id=category_id)

        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")

        return {"detail": "Category deleted successfully"}
