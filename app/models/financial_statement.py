import uuid

from sqlalchemy import UUID, Column, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    accession_number = Column(String, primary_key=True)
    period = Column(String, primary_key=True)
    filing_date = Column(String, primary_key=True)
    report_date = Column(String, primary_key=True)

    form = Column(String)
    value = Column(Numeric(38, 4))

    cik = Column(String, ForeignKey("companies.cik"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), primary_key=True)

    company = relationship("Company", back_populates="financial_statements")
    category = relationship("Category", back_populates="financial_statements")


class FMPStatement(Base):
    __tablename__ = "fmp_statements"

    period = Column(String, primary_key=True, index=True)
    filing_date = Column(String, nullable=False)
    report_date = Column(String, nullable=False)

    value = Column(Numeric(38, 4))

    cik = Column(String, ForeignKey("companies.cik"), primary_key=True, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("fmp_categories.id"), primary_key=True, index=True)

    company = relationship("Company", back_populates="fmp_statements")
    fmp_category = relationship("FMPCategory", back_populates="fmp_statements")


class FMPStatementV2(Base):
    __tablename__ = "fmp_statements_v2"
    __table_args__ = (
        UniqueConstraint("company_id", "period", "category_id", name="uq_company_id_period_category_id"),
        Index("idx_company_id_period_category_id", "company_id", "period", "category_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()")

    period = Column(String, index=True)

    filing_date = Column(String, nullable=False)
    report_date = Column(String, nullable=False)

    value = Column(Numeric(38, 4), nullable=False)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies_v2.id"), index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("fmp_categories.id"), index=True)

    company_v2 = relationship("CompanyV2", back_populates="fmp_statements_v2")
    fmp_category = relationship("FMPCategory", back_populates="fmp_statements_v2")
