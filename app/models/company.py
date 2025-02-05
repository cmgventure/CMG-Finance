from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Company(Base):
    __tablename__ = "companies"
    cik = Column(String, primary_key=True)
    name = Column(String)
    ticker = Column(String)
    sic = Column(String)
    business_address = Column(String)
    mailing_address = Column(String)
    phone = Column(String)
    sector = Column(String)
    industry = Column(String)
    country = Column(String)

    financial_statements = relationship("FinancialStatement", back_populates="company")
    fmp_statements = relationship("FMPStatement", back_populates="company")
