import asyncio
import time
from typing import Any
from uuid import UUID

import aiohttp
from fastapi import HTTPException
from loguru import logger
from starlette import status

from app.core.config import settings
from app.database.fmp_database import FMPDatabase
from app.enums.base import RequestMethod
from app.enums.fmp import FiscalPeriod
from app.schemas.fmp import FMPSchema
from app.schemas.schemas import FinancialStatementRequest, User
from app.services.financial_statement_service import FinancialStatementService, synchronized_request
from app.services.scheduler import scheduler_service
from app.utils.utils import apply_fiscal_period_patterns, parse_financial_statement_key


class FMPService(FinancialStatementService):
    def __init__(self, db: FMPDatabase, user: User) -> None:
        super().__init__(db, user)
        self.db = db
        self.api_url = "https://financialmodelingprep.com/api/v3"

    @staticmethod
    def extract_statements(statements: list[dict], categories: dict[str, UUID]) -> tuple[list[dict], bool]:
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
                if k in not_value_keys:
                    continue

                data: dict[str, Any] = {"value": str(round(v, 2))} | base
                if category_id := categories.get(k.lower()):
                    data["category_id"] = category_id
                else:
                    data["category"] = k
                    update_categories = True

                results.append(data)

        return results, update_categories

    @synchronized_request(lambda ticker: ticker)
    async def update_company_if_not_exists(self, ticker: str) -> str | None:
        cik = await self.db.get_company_cik(ticker=ticker)
        if not cik:
            await self.update_companies(ticker=ticker)
            cik = await self.db.get_company_cik(ticker=ticker)

        return cik

    async def update_companies(self, ticker: str | None = None) -> None:
        try:
            ciks = await self.get_all_company_ciks(ticker)

            if not ciks:
                return

            logger.info(f"CIKs found for {len(ciks)} companies")

            saved_ciks = await self.db.get_company_ciks()
            new_ciks = list(set(ciks) - set(saved_ciks))

            save_task = None
            for i in range(0, len(new_ciks), settings.COUNTER):
                fetch_start_time = time.time()
                tasks = [self.get_company_submissions(cik=cik) for cik in new_ciks[i : settings.COUNTER + i]]

                logger.info(f"Fetching data for {len(new_ciks[i:settings.COUNTER + i])} companies")

                submissions_list = list(filter(None, await asyncio.gather(*tasks)))
                companies = list(
                    filter(
                        None,
                        [self.extract_company_data(submissions) for submissions in submissions_list],
                    )
                )

                logger.info(f"Company data was fetched in {time.time() - fetch_start_time} seconds")

                if save_task:
                    await save_task

                logger.info(f"Saving data for {len(new_ciks[i:settings.COUNTER + i])} companies")

                save_task = asyncio.create_task(self.db.add_companies(companies))

            if save_task:
                await save_task

        except Exception as e:
            logger.error(f"Error updating companies: {e}")

        finally:
            logger.info("Finished updating companies")

    async def task_collect_financial_statement_value(self, data: FinancialStatementRequest) -> None:
        logger.info(f"Scraping data for {data.ticker} {data.category} {data.period}")

        cik = await self.update_company_if_not_exists(data.ticker)

        if not cik:
            logger.error(f"Company not found for stock ticker {data.ticker}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company not found for stock ticker {data.ticker}",
            )

        await self.get_statement(cik=cik, period=data.period)

        logger.info(f"Data scraped for {data.ticker} {data.category} {data.period}")

    async def get_financial_statement_by_key(self, key: str, force_update: bool) -> dict:
        parsed_request = parse_financial_statement_key(key)

        financial_statement = await self.get_financial_statement(parsed_request, force_update)
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

        # run bg task to calculate value
        scheduler_service.add_job(
            self.task_collect_financial_statement_value,
            id=f"{data.ticker}|{data.category}",
            misfire_grace_time=None,
            trigger="date",
            args=[data],
        )

    async def request(self, uri: str, method: RequestMethod = RequestMethod.GET, **kwargs: Any) -> dict:
        async with aiohttp.ClientSession() as session:
            params = kwargs.setdefault("params", {})
            params["apikey"] = settings.FMP_API_KEY

            response = await session.request(method=method, url=f"{self.api_url}/{uri}", **kwargs)
            return await response.json()

    async def get_statements(self, cik: str, period: FiscalPeriod, year: int | None = None) -> list[dict]:
        # limit = datetime.now(UTC).year - year + 1 if year else 100
        # if period.type == FiscalPeriodType.QUARTER:
        #     limit *= 4

        params = {"period": period.type}

        tasks = [
            self.request(f"{statement}/{cik}", params=params)
            for statement in ["income-statement", "balance-sheet-statement", "cash-flow-statement"]
        ]

        results = await asyncio.gather(*tasks)

        return [{k: v for statement in statements for k, v in statement.items()} for statements in zip(*results)]

    async def get_statement(self, cik: str, period: str) -> None:
        categories = await self.db.get_category_ids()

        period = apply_fiscal_period_patterns(period)
        fiscal_period, year = period.split()

        raw_statements = await self.get_statements(cik, FiscalPeriod(fiscal_period), int(year))
        statements, update_categories = self.extract_statements(raw_statements, categories)

        logger.info(
            f"Saving financial statements for company with CIK {cik} " f"and {len(statements)} financial statements"
        )
        await self.db.add_financial_statements(statements, update_categories)
