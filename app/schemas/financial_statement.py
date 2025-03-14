from typing import Self
from uuid import UUID

from pydantic import Field, constr, field_validator, model_validator

from app.enums.fiscal_period import FiscalPeriod, FiscalPeriodType
from app.schemas.base import Base, BaseRequest


class FinancialStatement(Base):
    cik: str
    period: str
    accession_number: str
    filing_date: str | None
    report_date: str | None
    category_id: UUID
    form: str | None
    value: float | None

    @field_validator("value", mode="before")
    @classmethod
    def convert_value(cls, value) -> float | None:
        if value is None:
            return None

        if isinstance(value, str) and value.startswith("$"):
            # Remove '$' and ',' then convert to float
            return float(value.replace("$", "").replace(",", ""))

        return float(value)


class FMPStatement(Base):
    id: UUID
    period: str
    filing_date: str | None
    report_date: str | None
    company_id: UUID
    category_id: UUID
    value: float | None

    @field_validator("value", mode="before")
    @classmethod
    def convert_value(cls, value) -> float | None:
        if value is None:
            return None

        if isinstance(value, str):
            # Remove '$' and ',' then convert to float
            return float(value.replace("$", "").replace(",", ""))

        return float(value)


class FinancialStatementRequest(BaseRequest):
    ticker: constr(to_upper=True)
    category: constr(to_lower=True)
    period: str = Field(default=str(FiscalPeriod.LATEST))

    @field_validator("period", mode="before")
    @classmethod
    def apply_period_patterns(cls, v) -> str:
        from app.utils.utils import apply_fiscal_period_patterns

        return apply_fiscal_period_patterns(v.upper()) if v else str(FiscalPeriod.LATEST)

    @property
    def period_type(self) -> FiscalPeriodType:
        fiscal_period = self.period.split()[0]
        return FiscalPeriod(fiscal_period).type

    @model_validator(mode="after")
    def validate_period_type(self) -> Self:
        try:
            _ = self.period_type
        except Exception:
            raise ValueError(f"Invalid period format: {self.period}")
        return self


class FinancialStatementsRequest(BaseRequest):
    keys: list[str]

    @property
    def parsed_keys(self) -> list[FinancialStatementRequest]:
        from app.utils.utils import parse_financial_statement_key

        return [parse_financial_statement_key(key) for key in self.keys]
