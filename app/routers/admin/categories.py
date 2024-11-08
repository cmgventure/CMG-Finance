import enum
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func, Enum, String, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.core.connection import get_db
from app.database.models import Category, User
from app.schemas.schemas import CategoryCreateSchema, CategoryUpdateSchema
from app.services.auth_service import get_current_user

categories_router = APIRouter(tags=["Admin Categories"])


column_names = [column.name for column in inspect(Category).columns]
CategoryColumns = enum.Enum("CategoryColumns", {name: name for name in column_names})


class SortOrder(str, enum.Enum):
    asc = "asc"
    desc = "desc"


@categories_router.get("/categories")
async def get_categories(
    page: int = 1,
    page_size: int = 100,
    sort_by: CategoryColumns | None = None,
    sort_order: SortOrder = SortOrder.asc,
    filter_by: CategoryColumns | None = None,
    filter_value: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # set the offset to start from
    offset = (page - 1) * page_size

    # create a base select query
    base_query = select(Category)
    # select_query = select(Category).offset(offset).limit(page_size)

    # if sort_by is passed, sort the query by the column
    if sort_by:
        if sort_order == "desc":
            base_query = base_query.order_by(getattr(Category, sort_by.value).desc())
        else:
            base_query = base_query.order_by(getattr(Category, sort_by.value))

    # if filter_by and filter_value are passed, filter the query by the column
    if filter_by and filter_value:
        column_attr = getattr(Category, filter_by.value)
        if isinstance(column_attr.type, Enum):
            base_query = base_query.filter(column_attr.cast(String).ilike(f"%{filter_value}%"))
        else:
            base_query = base_query.filter(column_attr.ilike(f"%{filter_value}%"))

    # get the categories records from the database
    paginated_query = base_query.offset(offset).limit(page_size)
    categories = (await db.execute(paginated_query)).scalars().all()

    # get the total count of categories
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar()

    return {"items": categories, "total": total}


@categories_router.get("/categories/{category_id}")
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = (await db.execute(select(Category).filter(Category.id == category_id))).scalar()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@categories_router.post("/categories")
async def create_category(
    category: CategoryCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_category = Category(**category.dict())
    db.add(db_category)
    try:
        await db.commit()
        await db.refresh(db_category)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e}")
    return db_category


@categories_router.patch("/categories/{category_id}")
async def update_category(
    category_id: UUID,
    category: CategoryUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_category = (await db.execute(select(Category).filter(Category.id == category_id))).scalars().first()

    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    obj_data = db_category.to_dict()

    update_data = category.model_dump(exclude_unset=True)

    for field in obj_data:
        if field in update_data:
            setattr(db_category, field, update_data[field])
    try:
        await db.commit()
        await db.refresh(db_category)
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e}")
    return db_category


@categories_router.delete("/categories/{category_id}")
async def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_category = (await db.execute(select(Category).filter(Category.id == category_id))).scalars().first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(db_category)
    await db.commit()
    return {"detail": "Category deleted successfully"}
