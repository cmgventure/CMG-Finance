import asyncio
from typing import Any
from uuid import UUID

import aiohttp
from fastapi import HTTPException
from loguru import logger
from starlette import status

from app.core.config import settings
from app.database.fmp_database import FMPDatabase
from app.enums.base import RequestMethod
from app.enums.fmp import FiscalPeriod, FiscalPeriodType
from app.schemas.fmp import FMPSchema
from app.schemas.schemas import FinancialStatementRequest
from app.services.scheduler import scheduler_service
from app.utils.utils import apply_fiscal_period_patterns, parse_financial_statement_key, synchronized_request


class FMPService:
    semaphore = asyncio.Semaphore(25)

    requests: dict = {}
    companies_update_task: asyncio.Task | None = None
    financial_statements_update_task: asyncio.Task | None = None

    def __init__(self, db: FMPDatabase) -> None:
        self.db = db
        self.api_url = "https://financialmodelingprep.com/api/v3"

    @staticmethod
    def extract_company_data(company: dict) -> dict | None:
        if not company["cik"]:
            return

        return {
            "cik": company["cik"],
            "name": company["companyName"],
            "ticker": company["symbol"],
            "business_address": company["address"],
            "mailing_address": company["address"],
            "phone": company["phone"],
        }

    @staticmethod
    def extract_statements(statements: list[dict], categories: dict[str, list[UUID]]) -> tuple[list[dict], bool]:
        not_value_keys = [
            "date",
            "symbol",
            "reportedCurrency",
            "cik",
            "fillingDate",
            "acceptedDate",
            "calendarYear",
            "period",
            "link",
            "finalLink",
        ]

        update_categories = False

        results = []
        for statement in statements:
            base = {
                "cik": statement["cik"],
                "period": f"{statement['period']} {statement['calendarYear']}",
                "report_date": statement["acceptedDate"],
                "filing_date": statement["fillingDate"],
            }

            for k, v in statement.items():
                if v is None or k in not_value_keys:
                    continue

                for category_id in categories.get(k.lower(), []):
                    results.append({"value": str(round(v, 2)), "category_id": category_id} | base)
                if not categories.get(k.lower()):
                    results.append({"value": str(round(v, 2)), "category": k} | base)
                    update_categories = True

        return results, update_categories

    @synchronized_request(lambda ticker: ticker)
    async def update_company_if_not_exists(self, ticker: str) -> str | None:
        cik = await self.db.get_company_cik(ticker=ticker)
        if not cik:
            await self.update_company(ticker=ticker)
            cik = await self.db.get_company_cik(ticker=ticker)

        return cik

    async def update_companies(self) -> None:
        companies = await self.request("stock/list")
        if not companies:
            return

        tickers = set(company["symbol"] for company in companies) - set(await self.db.get_company_tickers())

        tasks = [self.request(f"profile/{ticker}") for ticker in tickers]
        for i in range(0, len(tasks), 100):
            results = await asyncio.gather(*tasks[i : i + 100])
            companies_data = [
                data for company in results if company and (data := self.extract_company_data(company[0])) is not None
            ]

            logger.info(f"Get {len(companies_data)} companies data")

            if companies_data:
                await self.db.add_companies(companies_data)

            logger.info(f"Finished updating {i + 100} companies")

        logger.info("Finished updating companies")

    async def update_company(self, ticker: str) -> None:
        try:
            companies = await self.request(f"profile/{ticker}")
            if not companies:
                return

            company = companies[0]
            company_data = self.extract_company_data(company)

            logger.info(f"Get {ticker} company data")

            await self.db.add_company(company_data)
        except Exception as e:
            logger.error(f"Error updating company: {e}")

    async def task_collect_financial_statement_value(self, data: FinancialStatementRequest) -> None:
        logger.info(f"Scraping data for {data.ticker} {data.category} {data.period}")

        cik = await self.update_company_if_not_exists(data.ticker)

        if not cik:
            logger.error(f"Company not found for stock ticker {data.ticker}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company not found for stock ticker {data.ticker}",
            )

        await self.get_statement(ticker=data.ticker, period=data.period)

        logger.info(f"Data scraped for {data.ticker} {data.category} {data.period}")

    async def get_financial_statement_by_key(self, key: str, force_update: bool) -> dict:
        parsed_request = parse_financial_statement_key(key)

        financial_statement = await self.get_financial_statement(parsed_request, force_update=force_update)
        value = financial_statement.value if financial_statement else 0

        return {key: value}

    async def get_financial_statement(self, data: FinancialStatementRequest, force_update: bool) -> FMPSchema | None:
        # gets value from db or None
        if not force_update:
            financial_statement = await self.db.get_first_financial_statement_by_category_label(
                ticker=data.ticker, category_label=data.category, period=data.period
            )

            if financial_statement is not None:
                return financial_statement

        # at this point, we didn't get any values for all the specified tags of the category (sorted by priority)
        # we need to check if there are any formula type categories and calculate the value
        # if there are no formula type categories, we need to scrape the data
        period = apply_fiscal_period_patterns(data.period)
        fiscal_period, year = period.split()
        period_type = FiscalPeriod(fiscal_period).type

        # run bg task to calculate value
        scheduler_service.add_job(
            self.task_collect_financial_statement_value,
            id=f"{data.ticker}|{period_type}",
            misfire_grace_time=None,
            trigger="date",
            args=[data],
        )

    async def request(self, uri: str, method: RequestMethod = RequestMethod.GET, **kwargs: Any) -> dict:
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                params = kwargs.setdefault("params", {})
                params["apikey"] = settings.FMP_API_KEY

                response = await session.request(method=method, url=f"{self.api_url}/{uri}", **kwargs)
                return await response.json()

    async def fetch_statements(self, ticker: str, period_type: FiscalPeriodType, year: int | None = None) -> list[dict]:
        # limit = datetime.now(UTC).year - year + 1 if year else 100
        # if period.type == FiscalPeriodType.QUARTER:
        #     limit *= 4

        params = {"period": period_type}

        tasks = [
            self.request(f"{statement}/{ticker}", params=params)
            for statement in [
                "income-statement",
                "balance-sheet-statement",
                "cash-flow-statement",
                "key-metrics",
                "ratios",
            ]
        ]

        results = await asyncio.gather(*tasks)

        return [{k: v for statement in statements for k, v in statement.items()} for statements in zip(*results)]

    async def get_statement(self, ticker: str, period: str) -> None:
        categories = await self.db.get_category_ids()

        period = apply_fiscal_period_patterns(period)
        fiscal_period, year = period.split()

        raw_statements = await self.fetch_statements(ticker, FiscalPeriod(fiscal_period).type)
        statements, update_categories = self.extract_statements(raw_statements, categories)

        logger.info(
            f"Saving financial statements for company with ticker {ticker} "
            f"and {len(statements)} financial statements"
        )
        await self.db.add_financial_statements(statements, update_categories)

    async def get_statements(self):
        categories = await self.db.get_category_ids()

        tickers = await self.db.get_company_tickers()
        for ticker in tickers:
            for period_type in [FiscalPeriodType.ANNUAL, FiscalPeriodType.QUARTER]:
                raw_statements = await self.fetch_statements(ticker, period_type)
                statements, update_categories = self.extract_statements(raw_statements, categories)

                logger.info(
                    f"Saving financial statements for company with ticker {ticker} "
                    f"and {len(statements)} financial statements"
                )
                await self.db.add_financial_statements(statements, update_categories)

    async def start_companies_update(self) -> str:
        if FMPService.companies_update_task and not FMPService.companies_update_task.done():
            return "Companies data is being updated"

        FMPService.companies_update_task = asyncio.create_task(self.update_companies())
        return "Company data has started to be updated"

    async def start_financial_statements_update(self) -> str:
        if FMPService.financial_statements_update_task and not FMPService.financial_statements_update_task.done():
            return "Financial statements data is being updated"

        FMPService.financial_statements_update_task = asyncio.create_task(self.get_statements())
        return "Financial statements data has started to be updated"
