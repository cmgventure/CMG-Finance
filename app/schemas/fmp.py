from uuid import UUID

from pydantic import BaseModel, field_validator


class FMPSchema(BaseModel):
    cik: str
    period: str
    filing_date: str | None
    report_date: str | None
    category_id: UUID
    value: float | None

    class Config:
        from_attributes = True

    @field_validator("value", mode="before")
    @classmethod
    def convert_value(cls, value) -> float | None:
        if value is None:
            return None

        if isinstance(value, str):
            # Remove '$' and ',' then convert to float
            return float(value.replace("$", "").replace(",", ""))

        return float(value)
