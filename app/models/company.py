import uuid

from sqlalchemy import UUID, Column, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        Index("companies__cik", "cik"),
        Index("companies__ticker", "ticker"),
    )

    cik = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    sic = Column(String)
    business_address = Column(String)
    mailing_address = Column(String)
    phone = Column(String)
    sector = Column(String)
    industry = Column(String)
    country = Column(String)
    market_cap = Column(Numeric(38, 2))
    pe = Column(Numeric(38, 2), name="p/e", key="pe")
    price = Column(Numeric(38, 2))
    change = Column(Numeric(38, 2))
    volume = Column(Numeric(38, 2))

    financial_statements = relationship("FinancialStatement", back_populates="company")
    fmp_statements = relationship("FMPStatement", back_populates="company")


class CompanyV2(Base):
    __tablename__ = "companies_v2"
    __table_args__ = (
        UniqueConstraint("cik", "ticker", name="uq_cik_ticker"),
        Index("idx_cik_ticker", "cik", "ticker"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")

    cik = Column(String, nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)

    sic = Column(String)
    business_address = Column(String)
    mailing_address = Column(String)
    phone = Column(String)
    sector = Column(String)
    industry = Column(String)
    country = Column(String)

    market_cap = Column(Numeric(38, 2))
    pe = Column(Numeric(38, 2), name="p/e", key="pe")
    price = Column(Numeric(38, 2))
    change = Column(Numeric(38, 2))
    volume = Column(Numeric(38, 2))

    fmp_statements_v2 = relationship("FMPStatementV2", back_populates="company_v2")
