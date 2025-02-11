import uuid

from sqlalchemy import UUID, CheckConstraint, Column, Enum, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.enums.category import CategoryDefinitionType
from app.models.base import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("priority >= 1"),
        UniqueConstraint("label", "value_definition", "type", name="uq_label_value_definition_type"),
    )

    id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    label = Column(String)
    value_definition = Column(String)
    description = Column(String, nullable=True)
    type = Column(Enum(CategoryDefinitionType), nullable=True, default=CategoryDefinitionType.api_tag)
    priority = Column(Integer, nullable=False, default=1)

    financial_statements = relationship(
        "FinancialStatement",
        back_populates="category",
        cascade="save-update, merge, delete, delete-orphan",
    )


class FMPCategory(Base):
    __tablename__ = "fmp_categories"
    __table_args__ = (
        CheckConstraint("priority >= 1"),
        UniqueConstraint("label", "value_definition", name="uq_label_value_definition"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    label = Column(String)
    value_definition = Column(String)
    description = Column(String, nullable=True)
    type = Column(
        Enum(CategoryDefinitionType, name="fmpcategorydefinitiontype"),
        nullable=True,
        default=CategoryDefinitionType.api_tag,
    )
    priority = Column(Integer, nullable=False, default=1)

    fmp_statements = relationship(
        "FMPStatement",
        back_populates="fmp_category",
        cascade="save-update, merge, delete, delete-orphan",
    )
