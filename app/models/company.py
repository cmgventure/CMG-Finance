from sqlalchemy import Column, Index, Integer, Numeric, String
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
    pe = Column(Numeric(38, 2), name="P/E", key="pe")
    price = Column(Numeric(38, 2))
    change = Column(Numeric(38, 2))
    volume = Column(Integer)

    financial_statements = relationship("FinancialStatement", back_populates="company")
    fmp_statements = relationship("FMPStatement", back_populates="company")
