from app.enums.base import BaseStrEnum


class FiscalPeriodType(BaseStrEnum):
    TTM = "ttm"
    ANNUAL = "annual"
    QUARTER = "quarter"


class FiscalPeriod(BaseStrEnum):
    TTM = "TTM"
    FY = "FY"
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"

    @property
    def type(self) -> FiscalPeriodType:
        if self == FiscalPeriod.TTM:
            return FiscalPeriodType.TTM
        elif self == FiscalPeriod.FY:
            return FiscalPeriodType.ANNUAL
        else:
            return FiscalPeriodType.QUARTER
