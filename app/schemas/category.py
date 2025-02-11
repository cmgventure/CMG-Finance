from uuid import UUID

from app.enums.category import CategoryDefinitionType
from app.schemas.base import Base, BaseRequest


class Category(Base):
    id: UUID
    label: str
    value_definition: str
    description: str
    type: CategoryDefinitionType
    priority: int


class CategoryCreateRequest(BaseRequest):
    label: str
    value_definition: str
    description: str
    type: CategoryDefinitionType
    priority: int


class CategoryUpdateRequest(BaseRequest):
    label: str | None = None
    value_definition: str | None = None
    description: str | None = None
    type: CategoryDefinitionType | None = None
    priority: int | None = None
