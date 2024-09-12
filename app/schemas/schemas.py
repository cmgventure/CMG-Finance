from enum import IntEnum, StrEnum

from pydantic import BaseModel

category_map = {
    "AccruedIncomeTaxesCurrent": "Interest Expense",
    "AmortizationAndImpairmentOfIntangibleAssets": "Amortization",
    "Assets": "Total Assets",
    "AssetsCurrent": "Total Current Assets",
    "AvailableForSaleSecuritiesCurrent": "Marketable Securities",
    "CashAndCashEquivalentsAtCarryingValue": "Free Cash Flow",
    "CashAndCashEquivalentsPeriodIncreaseDecrease": "Net Change in Cash",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": "Free Cash Flow",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect": "Net Change in Cash",
    "CommunicationsAndInformationTechnology": "Communications and Information Technology",
    "CostOfGoodsAndServicesSold": "Cost Of Revenue",
    "CostOfRevenue": "Cost Of Revenue",
    "Depreciation": "Depreciation and amortization",
    "DepreciationAndAmortization": "Depreciation and amortization",
    "DepreciationDepletionAndAmortization": "Depreciation and amortization",
    "DepreciationAmortizationAndAccretionNet": "Depreciation and amortization",
    "DepreciationAndImpairmentOnDispositionOfPropertyAndEquipment": "Depreciation",
    "EarningsPerShareDiluted": "Earnings Per Share",
    "EBITDA": "EBITDA",
    "FreeCashFlow": "Free Cash Flow",
    "GrossProfit": "Gross Profit",
    "IncomeTaxesPaidNet": "Income Taxes",
    "InterestPaid": "Interest Expense",
    "InterestPaidNet": "Interest Expense",
    "Investments": "Marketable Securities",
    "LaborAndRelatedExpense": "Labor and Related Expense",
    "Liabilities": "Total Liabilities",
    "LiabilitiesAndStockholdersEquity": "Liabilities and Equity",
    "LiabilitiesCurrent": "Total Current Liabilities",
    "LeaseLiabilityNoncurrent": "Lease Liability",
    "LongTermDebt": "Long Term Debt Current",
    "LongTermDebtNoncurrent": "Long Term Debt",
    "MarketableSecuritiesCurrent": "Marketable Securities",
    "NetCashProvidedByUsedInOperatingActivities": "Operating Cash Flow",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": "Operating Cash Flow",
    "NetIncomeLoss": "Net Income",
    "OperatingIncomeLoss": "Operating Income",
    "OtherLiabilitiesNoncurrent": "Other Liabilities",
    "PaymentsOfDividendsCommonStock": "Dividends Paid",
    "PaymentsForRepurchaseOfCommonStock": "Common Stock Repurchased",
    "PaymentsOfDividends": "Dividends Paid",
    "PaymentsToAcquireProductiveAssets": "Capital Expenditure",
    "PaymentsToAcquirePropertyPlantAndEquipment": "Capital Expenditure",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "Revenue",
    "Revenues": "Revenue",
    "SalesRevenueNet": "Revenue",
    "StockRepurchasedDuringPeriodValue": "Common Stock Repurchased",
    "StockRepurchasedAndRetiredDuringPeriodValue": "Common Stock Repurchased",
    "StockholdersEquity": "Total Equity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "Total Equity",
    "TotalLiabilities": "Total Liabilities",
    "TreasuryStockValueAcquiredCostMethod": "Common Stock Repurchased",
    "WeightedAverageNumberOfSharesOutstandingBasic": "Shares Outstanding",
}

# [] - sum
# () - difference
calculation_map = {
    "CostOfRevenue": [
        ("Revenue", "Gross Profit"),
    ],
    "DepreciationAndAmortization": [
        ["Depreciation", "Amortization"],
    ],
    "EBITDA": [
        [
            "Net Income",
            "Interest Expense",
            "Income Taxes",
            "Depreciation and amortization",
        ],
    ],
    "FreeCashFlow": [
        ("Operating Cash Flow", "Capital Expenditure"),
    ],
    "GrossProfit": [
        ["Labor and Related Expense", "Communications and Information Technology"],
        ("Revenue", "Cost Of Revenue"),
    ],
    "TotalLiabilities": [
        ("Liabilities and Equity", "Total Equity"),
        # ["Total Current Liabilities", "Lease Liability", "Long Term Debt", "Other Liabilities"]
    ],
}


class FulfillmentStatus(StrEnum):
    PENDING = "PENDING"
    CANCELED = "CANCELED"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"


class ProductId(StrEnum):
    Free = "66b288c881b4155bf9e53c57"
    Basic = "073642cd-7456-4c26-8158-66a9b440ecda"
    Premium = "0fbcfeb2-b8bc-4211-8108-d87de08f24e0"


class SubscriptionType(StrEnum):
    Free = "Free Trial"
    Basic = "Basic Subscription"
    Premium = "Premium Subscription"
    AnnualBasic = "Basic Subscription"
    AnnualPremium = "Premium Subscription"


class User(BaseModel):
    id: str
    email: str
    subscription: dict | None = None
    superuser: bool = False


class FinancialStatementRequest(BaseModel, str_strip_whitespace=True):
    ticker: str
    category1: str
    period: str


class FinancialStatementsUpdateRequest(BaseModel, str_strip_whitespace=True):
    ticker: str | None = None
    category: str | None = None


class CompaniesUpdateRequest(BaseModel, str_strip_whitespace=True):
    ticker: str | None = None
