import asyncio
from typing import Any
from uuid import UUID, uuid4

import aiohttp
from aiohttp import ClientResponseError
from fastapi import HTTPException
from loguru import logger
from starlette import status

from app.core.config import settings
from app.enums.base import RequestMethod
from app.enums.category import CategoryDefinitionType
from app.enums.fiscal_period import FiscalPeriod, FiscalPeriodType
from app.models.company import Company
from app.models.financial_statement import FMPStatement
from app.schemas.financial_statement import FinancialStatementRequest, FinancialStatementsRequest
from app.utils.unitofwork import ABCUnitOfWork, UnitOfWork
from app.utils.utils import parse_financial_statement_key, synchronized_request, transform_category


class FMPService:
    api_url = "https://financialmodelingprep.com/api"

    semaphore = asyncio.Semaphore(25)

    requests: dict = {}
    companies_update_task: asyncio.Task | None = None
    financial_statements_update_task: asyncio.Task | None = None

    async def request(self, uri: str, method: RequestMethod = RequestMethod.GET, **kwargs: Any) -> dict:
        params = kwargs.setdefault("params", {})
        params["apikey"] = settings.FMP_API_KEY
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.request(method=method, url=f"{self.api_url}/{uri}", **kwargs)
                await response.read()
                response.raise_for_status()
                return await response.json()
            except ClientResponseError:
                logger.error(f"{method} {self.api_url}/{uri} {response.status} - Failed")
                raise HTTPException(status_code=response.status, detail=await response.text())

    @staticmethod
    def _extract_company_data(company: dict) -> dict | None:
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
    def _extract_statements(
        statements: list[dict],
        category_ids: dict[str, list[UUID]],
        period_type: FiscalPeriodType,
        cik: str | None = None,
    ) -> tuple[list[dict], list[dict]]:
        not_value_keys = {
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
            "label",
            "recordDate",
            "paymentDate",
            "declarationDate",
        }

        categories_to_update = []
        results = []
        historical_results = {}

        for statement in statements:
            if period_type in (FiscalPeriodType.LATEST, FiscalPeriodType.TTM):
                cik = cik or statement.get("cik")
                base = {
                    "cik": cik,
                    "period": period_type,
                    "report_date": period_type,
                    "filing_date": period_type,
                }
            elif period_type == FiscalPeriodType.HISTORICAL:
                year = statement["date"].split("-")[0]
                base = {
                    "cik": cik,
                    "period": f"{FiscalPeriod.FY} {year}",
                    "report_date": statement["date"],
                    "filing_date": statement["date"],
                }
            else:
                base = {
                    "cik": cik,
                    "period": f"{statement['period']} {statement['calendarYear']}",
                    "report_date": statement["date"],
                    "filing_date": statement["fillingDate"],
                }

            for k, v in statement.items():
                if v is None or k in not_value_keys:
                    continue

                value = round(v, 4)

                if not category_ids.get(k.lower()):
                    category_id = uuid4()
                    category_ids[k.lower()] = [category_id]
                    categories_to_update.append(
                        {
                            "id": category_id,
                            "label": transform_category(k),
                            "value_definition": k,
                            "description": k,
                            "type": CategoryDefinitionType.api_tag,
                            "priority": 1,
                        }
                    )

                for category_id in category_ids.get(k.lower(), []):
                    result = {"value": str(value), "category_id": category_id} | base
                    if period_type != FiscalPeriodType.HISTORICAL:
                        results.append(result)
                        continue

                    key = f"{result['period']}_{category_id}"
                    if historical_result := historical_results.get(key):
                        historical_result["value"] = str(round(float(historical_result["value"]) + value, 4))
                    else:
                        historical_results[key] = result

        results.extend(historical_results.values())

        return results, categories_to_update

    @staticmethod
    async def _get_financial_statement(data: FinancialStatementRequest) -> FMPStatement | None:
        async with UnitOfWork() as unit_of_work:
            return await unit_of_work.financial_statement.get_one_or_none(
                ticker=data.ticker, label=data.category.lower(), period__ilike=data.period.lower()
            )

    async def get_financial_statements(
        self,
        data: FinancialStatementsRequest,
        force_update: bool = False,
        wait_response: bool = False,
    ) -> dict:
        logger.info(f"Accepted request with {len(data.keys)} keys: {data.keys}")

        parsed_statements = {}

        tasks = [self.get_financial_statement_by_key(key, force_update, wait_response) for key in data.keys]
        for statement in await asyncio.gather(*tasks):
            parsed_statements.update(statement)

        logger.info(f"Parsed {len(parsed_statements)} statements: {parsed_statements}")

        return parsed_statements

    async def get_financial_statement_by_key(
        self, key: str, force_update: bool = False, wait_response: bool = False
    ) -> dict[str, float | None]:
        data = parse_financial_statement_key(key)
        try:
            value = await self.get_financial_statement(data, force_update, wait_response)
        except HTTPException as e:
            logger.error(e.detail)
            value = None
        except Exception as e:
            logger.error(str(e))
            value = None

        return {key: value}

    async def get_financial_statement(
        self,
        data: FinancialStatementRequest,
        force_update: bool = False,
        wait_response: bool = False,
    ) -> float | None:
        logger.info(f"Accepted {data} request")

        if data.period_type == FiscalPeriodType.TTM and not data.category.endswith("ttm"):
            data.category = f"{data.category} ttm"

        if not force_update:
            # gets value from db or None
            financial_statement = await self._get_financial_statement(data)
            if financial_statement is not None:
                return financial_statement.value

        # at this point, we didn't get any values for all the specified tags of the category (sorted by priority)
        # we need to check if there are any formula type categories and calculate the value
        # if there are no formula type categories, we need to scrape the data
        value = None
        key = f"{data.ticker}|{data.period_type}"
        if wait_response:
            logger.info(f"Updating financial statement, {key=}")
            await self.update_financial_statement(data, key=key)
            financial_statement = await self._get_financial_statement(data)
            value = financial_statement.value if financial_statement else None
        else:
            # run bg task to calculate value
            logger.info(f"Creating financial statement update task, {key=}")
            task = asyncio.create_task(self.update_financial_statement(data, key=key))

        return value

    @synchronized_request
    async def update_financial_statement(self, data: FinancialStatementRequest) -> None:
        async with UnitOfWork() as unit_of_work:
            cik = await self.update_company_if_not_exists(unit_of_work, data.ticker)
            if not cik:
                logger.error(f"Company not found for stock ticker {data.ticker}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Company not found for stock ticker {data.ticker}",
                )

            logger.info(f"Scraping data for {data.ticker} {data.period_type}")

            await self.add_statement(unit_of_work, cik=cik, ticker=data.ticker, period=data.period)

            logger.info(f"Data scraped for {data.ticker} {data.period_type}")

    async def update_company_if_not_exists(self, unit_of_work: ABCUnitOfWork, ticker: str) -> str | None:
        company = await unit_of_work.company.get_one_or_none(ticker=ticker)
        if not company:
            key = ticker
            logger.info(f"Updating company, {key=}")
            await self.add_company(unit_of_work, ticker=ticker, key=key)
            company = await unit_of_work.company.get_one_or_none(ticker=ticker)

        return company.cik if company else None

    @synchronized_request
    async def add_company(self, unit_of_work: ABCUnitOfWork, ticker: str) -> Company | None:
        companies = await self.request(f"v3/profile/{ticker}")
        if not companies:
            return

        company = companies[0]
        company_data = self._extract_company_data(company)

        logger.info(f"Get {ticker} company data")

        return await unit_of_work.company.create(company_data)

    async def fetch_statements(self, ticker: str, period_type: FiscalPeriodType, year: int | None = None) -> list[dict]:
        # limit = datetime.now(UTC).year - year + 1 if year else 100
        # if period.type == FiscalPeriodType.QUARTER:
        #     limit *= 4

        if period_type == FiscalPeriodType.LATEST:
            tasks = [
                self.request(statement)
                for statement in [f"v3/discounted-cash-flow/{ticker}", f"v4/price-target-consensus?symbol={ticker}"]
            ]
        elif period_type == FiscalPeriodType.TTM:
            tasks = [self.request(f"v3/{statement}/{ticker}") for statement in ["key-metrics-ttm", "ratios-ttm"]]
        elif period_type == FiscalPeriodType.HISTORICAL:
            tasks = [
                self.request(f"v3/{statement}/{ticker}")
                for statement in [
                    "historical-price-full/stock_dividend",
                ]
            ]
        else:
            params = {"period": period_type}

            tasks = [
                self.request(f"v3/{statement}/{ticker}", params=params)
                for statement in [
                    "income-statement",
                    "balance-sheet-statement",
                    "cash-flow-statement",
                    "income-statement-growth",
                    "balance-sheet-statement-growth",
                    "cash-flow-statement-growth",
                    "key-metrics",
                    "ratios",
                ]
            ]

        results = await asyncio.gather(*tasks)
        if period_type == FiscalPeriodType.HISTORICAL:
            results = [result.get("historical") for result in results]
        results = list(filter(None, results))

        return [{k: v for statement in statements for k, v in statement.items()} for statements in zip(*results)]

    async def add_statement(
        self, unit_of_work: ABCUnitOfWork, cik: str, ticker: str, period: str | None = None
    ) -> None:
        if period:
            fiscal_period = period.split()[0]
            period_type = FiscalPeriod(fiscal_period).type
        else:
            period_type = FiscalPeriodType.LATEST

        categories = await unit_of_work.category.get_multi()

        category_ids = {}
        for category in categories:
            category_ids.setdefault(category.value_definition.lower(), []).append(category.id)

        raw_statements = await self.fetch_statements(ticker, period_type)

        statements, categories_to_update = self._extract_statements(raw_statements, category_ids, period_type, cik)
        if period_type == FiscalPeriodType.ANNUAL:
            raw_historical_statements = await self.fetch_statements(ticker, FiscalPeriodType.HISTORICAL)
            historical_statements, historical_categories_to_update = self._extract_statements(
                raw_historical_statements, category_ids, FiscalPeriodType.HISTORICAL, cik
            )
            statements.extend(historical_statements)
            categories_to_update.extend(historical_categories_to_update)

        logger.info(
            f"Saving financial statements for company with ticker {ticker} "
            f"and {len(statements)} financial statements"
        )
        if categories_to_update:
            await unit_of_work.category.create_many(categories_to_update)
        await unit_of_work.financial_statement.create_many(statements)

    async def add_companies(self) -> None:
        companies = await self.request("v3/stock/list")
        if not companies:
            return

        async with UnitOfWork() as unit_of_work:
            tickers = set(company["symbol"] for company in companies) - set(await unit_of_work.company.get_tickers())

            tasks = [self.request(f"v3/profile/{ticker}") for ticker in tickers]
            for i in range(0, len(tasks), 100):
                results = await asyncio.gather(*tasks[i : i + 100])
                companies_data = [
                    data
                    for company in results
                    if company and (data := self._extract_company_data(company[0])) is not None
                ]

                logger.info(f"Get {len(companies_data)} companies data")

                if companies_data:
                    await unit_of_work.company.create_many(companies_data)

                logger.info(f"Finished updating {i + 100} companies")

            logger.info("Finished updating companies")

    async def add_statements(self) -> None:
        async with UnitOfWork() as unit_of_work:
            categories = await unit_of_work.category.get_multi()

            category_ids = {}
            for category in categories:
                category_ids.setdefault(category.value_definition.lower(), []).append(category.id)

            companies = await unit_of_work.company.get_unfilled_companies()
            for company in companies:
                for period_type in FiscalPeriodType.list():
                    try:
                        raw_statements = await self.fetch_statements(company.ticker, period_type)
                        statements, categories_to_update = self._extract_statements(
                            raw_statements, category_ids, period_type, company.cik
                        )

                        logger.info(
                            f"Saving {period_type} financial statements for company with ticker {company.ticker} "
                            f"and {len(statements)} financial statements"
                        )
                        if categories_to_update:
                            await unit_of_work.category.create_many(categories_to_update)
                        await unit_of_work.financial_statement.create_many(statements)
                        await unit_of_work.session.commit()
                    except Exception as e:
                        logger.error(f"Error while updating financial statements for company {company.ticker}: {e}")

            logger.info("Finished updating financial statements")

    async def start_companies_update(self) -> str:
        if FMPService.companies_update_task and not FMPService.companies_update_task.done():
            return "Companies data is being updated"

        FMPService.companies_update_task = asyncio.create_task(self.add_companies())
        return "Company data has started to be updated"

    async def start_financial_statements_update(self) -> str:
        if FMPService.financial_statements_update_task and not FMPService.financial_statements_update_task.done():
            return "Financial statements data is being updated"

        FMPService.financial_statements_update_task = asyncio.create_task(self.add_statements())
        return "Financial statements data has started to be updated"
