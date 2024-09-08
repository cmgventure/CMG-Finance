from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app.schemas.schemas import FulfillmentStatus, SubscriptionType

Base = declarative_base()


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

    tag = Column(String, primary_key=True)
    category = Column(String)
    label = Column(String, nullable=True)

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
    tag = Column(String, ForeignKey("categories.tag"), primary_key=True)

    company = relationship("Company", back_populates="financial_statements")
    category = relationship("Category", back_populates="financial_statements")
