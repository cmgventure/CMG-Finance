from app.enums.base import BaseStrEnum


class FiscalPeriodType(BaseStrEnum):
    HISTORICAL = "historical"
    LATEST = "latest"
    TTM = "ttm"
    ANNUAL = "annual"
    QUARTER = "quarter"


class FiscalPeriod(BaseStrEnum):
    HISTORICAL = "HISTORICAL"
    LATEST = "LATEST"
    TTM = "TTM"
    FY = "FY"
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"

    @property
    def type(self) -> FiscalPeriodType:
        if self == FiscalPeriod.FY:
            return FiscalPeriodType.ANNUAL
        elif self.startswith("Q"):
            return FiscalPeriodType.QUARTER
        else:
            return FiscalPeriodType[self]
