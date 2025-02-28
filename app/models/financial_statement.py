from sqlalchemy import UUID, Column, ForeignKey, Numeric, String
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

    period = Column(String, primary_key=True)
    filing_date = Column(String, primary_key=True)
    report_date = Column(String, primary_key=True)

    value = Column(Numeric(38, 4))

    cik = Column(String, ForeignKey("companies.cik"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("fmp_categories.id"), primary_key=True)

    company = relationship("Company", back_populates="fmp_statements")
    fmp_category = relationship("FMPCategory", back_populates="fmp_statements")
