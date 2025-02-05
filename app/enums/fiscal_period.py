from app.enums.base import BaseStrEnum


class FiscalPeriodType(BaseStrEnum):
    LATEST = "latest"
    TTM = "ttm"
    ANNUAL = "annual"
    QUARTER = "quarter"


class FiscalPeriod(BaseStrEnum):
    LATEST = "LATEST"
    TTM = "TTM"
    FY = "FY"
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"

    @property
    def type(self) -> FiscalPeriodType:
        if self == FiscalPeriod.LATEST:
            return FiscalPeriodType.LATEST
        elif self == FiscalPeriod.TTM:
            return FiscalPeriodType.TTM
        elif self == FiscalPeriod.FY:
            return FiscalPeriodType.ANNUAL
        else:
            return FiscalPeriodType.QUARTER
