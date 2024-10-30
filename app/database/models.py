import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UUID,
)
from sqlalchemy.orm import relationship

from app.database.base_class import Base
from app.schemas.schemas import FulfillmentStatus, SubscriptionType


class CategoryDefinitionType(StrEnum):
    api_tag = "api-tag"
    custom_formula = "custom-formula"
    exact_value = "exact-value"


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String)
    superuser = Column(Boolean, default=False)

    subscriptions = relationship("Subscription", back_populates="user")


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True)
    transaction_id = Column(String)
    type = Column(Enum(SubscriptionType))
    status = Column(Enum(FulfillmentStatus))
    created_at = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime)

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)

    user = relationship("User", back_populates="subscriptions")


class Company(Base):
    __tablename__ = "companies"
    cik = Column(String, primary_key=True)
    name = Column(String)
    ticker = Column(String)
    sic = Column(String)
    business_address = Column(String)
    mailing_address = Column(String)
    phone = Column(String)

    financial_statements = relationship("FinancialStatement", back_populates="company")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("priority >= 1"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4, server_default="gen_random_uuid()")
    label = Column(String)
    value_definition = Column(String)
    description = Column(String, nullable=True)
    type = Column(Enum(CategoryDefinitionType), nullable=True, default=CategoryDefinitionType.api_tag)
    priority = Column(Integer, nullable=False, default=1)

    financial_statements = relationship("FinancialStatement", back_populates="category")


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    accession_number = Column(String, primary_key=True)
    period = Column(String, primary_key=True)
    filing_date = Column(String, primary_key=True)
    report_date = Column(String, primary_key=True)

    form = Column(String)
    value = Column(Float)

    cik = Column(String, ForeignKey("companies.cik"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), primary_key=True)

    company = relationship("Company", back_populates="financial_statements")
    category = relationship("Category", back_populates="financial_statements")
