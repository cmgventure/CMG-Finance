from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.core.connection import get_db
from app.database.models import Category, User
from app.schemas.schemas import CategoryCreateSchema, CategoryUpdateSchema
from app.services.auth_service import get_current_user

categories_router = APIRouter(tags=["Admin Categories"])


@categories_router.get("/categories")
async def get_categories(
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    offset = (page - 1) * page_size
    select_query = select(Category).offset(offset).limit(page_size)
    categories = (await db.execute(select_query)).scalars().all()
    count_query = select(func.count()).select_from(Category)
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
