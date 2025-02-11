from app.models.category import FMPCategory
from app.repository.base import SQLAlchemyRepository


class CategoryRepository(SQLAlchemyRepository[FMPCategory]):
    model = FMPCategory
