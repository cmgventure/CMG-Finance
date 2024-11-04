from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.connection import get_db
from app.database.models import Category
from app.schemas.schemas import CategoryCreateSchema

categories_router = APIRouter()


@categories_router.get("/categories")
async def get_categories(page: int = 1, page_size: int = 100, db: Session = Depends(get_db)):
    offset = (page - 1) * page_size
    categories = db.query(Category).offset(offset).limit(page_size).all()
    total = db.query(Category).count()
    return {"items": categories, "total": total}


@categories_router.get("/categories/{category_id}")
async def get_category(category_id: UUID, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@categories_router.post("/categories")
async def create_category(category: CategoryCreateSchema, db: Session = Depends(get_db)):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@categories_router.put("/categories/{category_id}")
async def update_category(category_id: UUID, category: CategoryCreateSchema, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category


@categories_router.delete("/categories/{category_id}")
async def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()
    return {"detail": "Category deleted successfully"}
