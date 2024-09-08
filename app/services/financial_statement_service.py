import asyncio
import time
from functools import wraps

import aiohttp
from aiohttp import ClientError
from fastapi import HTTPException
from sec_edgar_api import EdgarClient
from starlette import status

from app.core.config import logger, settings
from app.database.database import Database
from app.database.models import FinancialStatement
from app.schemas.schemas import (
    FinancialStatementRequest,
    User,
    calculation_map,
    category_map,
)


def synchronized_request(key_func):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            key = key_func(*args)
            requests = FinancialStatementService.requests

            if key in requests:
                await requests[key].wait()
                logger.info(f"Waiting for {key}")
            else:
                requests[key] = asyncio.Event()

            try:
                result = await func(self, *args, **kwargs)
            finally:
                if key in requests:
                    event = requests.pop(key)
                    event.set()

            return result

        return wrapper

    return decorator


class FinancialStatementService:
    semaphore = asyncio.Semaphore(settings.counter)

    requests: dict = {}
    companies_update_task: asyncio.Task | None = None
    financial_statements_update_task: asyncio.Task | None = None

    def __init__(self, db: Database, user: User) -> None:
        self.db = db
        self.user_agent = user.email
        self.edgar_client = EdgarClient(user_agent=self.user_agent)

    @synchronized_request(lambda data: f"{data.ticker} {data.category}")
    async def get_financial_statement(
        self, data: FinancialStatementRequest, root_categories: set[str] | None = None
    ) -> FinancialStatement | None:
        financial_statement = await self.find_financial_statement(data, root_categories)
        if not financial_statement:
            cik = await self.update_company_if_not_exists(data.ticker)
            if not cik:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Company not found for stock ticker {data.ticker}",
                )

            await self.update_financial_statements(cik=cik, category=data.category)
            financial_statement = await self.find_financial_statement(
                data, root_categories
            )

        return financial_statement

    async def calculate_financial_statement(
        self, data: FinancialStatementRequest, root_categories: set[str]
    ):
        for k, v in calculation_map.items():
            tag = k
            if data.category.lower() == category_map.get(tag, "").lower():
                conditions = v
                break
        else:
            return

        for condition in conditions:
            if root_categories.intersection(condition):
                continue

            financial_statements = [
                await self.get_financial_statement(
                    FinancialStatementRequest(
                        ticker=data.ticker,
                        category=value,
                        period=data.period,
                    ),
                    root_categories=root_categories.copy(),
                )
                for value in condition
            ]
            if not all(financial_statements):
                continue

            if isinstance(condition, list):
                value = sum(
                    [
                        financial_statement.value
                        for financial_statement in financial_statements
                    ]
                )
            else:
                value = financial_statements[0].value - sum(
                    [
                        financial_statement.value
                        for financial_statement in financial_statements[1:]
                    ]
                )

            financial_statement = await self.db.update_category_value(
                financial_statements[0], tag, value
            )
            return financial_statement

    async def find_financial_statement(
        self, data: FinancialStatementRequest, root_categories: set[str] | None = None
    ) -> FinancialStatement | None:
        financial_statement = await self.db.find_financial_statement(
            data.ticker, data.category, data.period
        )
        if financial_statement:
            return financial_statement

        if not root_categories:
            root_categories = {data.category}
        else:
            root_categories.add(data.category)

        return await self.calculate_financial_statement(data, root_categories)

    @synchronized_request(lambda ticker: ticker)
    async def update_company_if_not_exists(self, ticker: str) -> str | None:
        cik = await self.db.get_company_cik(ticker=ticker)
        if not cik:
            await self.update_companies(ticker=ticker)
            cik = await self.db.get_company_cik(ticker=ticker)

        return cik

    async def get_all_company_ciks(self, ticker: str | None) -> list[str] | None:
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {"User-Agent": self.user_agent}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
            if ticker:
                for company in data.values():
                    if company["ticker"] == ticker:
                        return [str(company["cik_str"]).zfill(10)]
            else:
                return [str(company["cik_str"]).zfill(10) for company in data.values()]
        except ClientError as e:
            logger.error(f"Error fetching company CIKs: {e}")

    async def get_company_submissions(self, cik: str) -> dict | None:
        async with self.semaphore:
            try:
                response = await asyncio.to_thread(
                    self.edgar_client.get_submissions, cik=cik
                )
                return response
            except Exception as e:
                logger.error(f"Error fetching company submissions for CIK {cik}: {e}")

    async def get_company_facts(self, cik: str) -> dict | None:
        async with self.semaphore:
            try:
                response = await asyncio.to_thread(
                    self.edgar_client.get_company_facts, cik=cik
                )
                return response.get("facts", {})
            except Exception as e:
                logger.error(f"Error fetching company submissions for CIK {cik}: {e}")

    async def get_company_concept(
        self, cik: str, taxonomy: str, tag: str
    ) -> dict | None:
        async with self.semaphore:
            try:
                response = await asyncio.to_thread(
                    self.edgar_client.get_company_concept,
                    cik=cik,
                    taxonomy=taxonomy,
                    tag=tag,
                )
                return response
            except Exception as e:
                logger.error(f"Error fetching company concept for CIK {cik}: {e}")

    @staticmethod
    def extract_company_data(submissions: dict) -> dict | None:
        try:
            ticker = None
            if not submissions["tickers"]:
                filings = submissions.get("filings", {}).get("recent", {})
                forms = filings.get("form", [])
                documents = filings.get("primaryDocument")
                for form, document in zip(forms, documents):
                    if form in ["10-Q", "10-K"]:
                        ticker = document.split("-")[0].upper()
                        break
            else:
                ticker = submissions["tickers"][0]

            if not ticker:
                return

            data = {
                "cik": submissions["cik"].zfill(10),
                "name": submissions["name"],
                "ticker": ticker,
                "sic": submissions["sic"],
                "business_address": submissions["addresses"]["business"]["street1"],
                "mailing_address": submissions["addresses"]["mailing"]["street1"],
                "phone": submissions["phone"],
            }
            return data
        except Exception as e:
            logger.error(f"Error extracting company data: {e}")

    @staticmethod
    def extract_financial_statements(concept: dict) -> list:
        try:
            financial_statements = []
            for unit_data in concept.get("units", {}).values():
                for financial_statement in unit_data:
                    if financial_statement["form"] not in ["10-Q", "10-K"]:
                        continue

                    data = {
                        "cik": str(concept["cik"]).zfill(10),
                        "accession_number": financial_statement["accn"],
                        "period": f"{financial_statement['fp']} {financial_statement['fy']}",
                        "report_date": financial_statement["end"],
                        "filing_date": financial_statement["filed"],
                        "tag": concept["tag"],
                        # "label": concept["label"],
                        "form": financial_statement["form"],
                        "value": financial_statement["val"],
                    }
                    financial_statements.append(data)

            return financial_statements
        except Exception as e:
            logger.error(f"Error extracting financial statements: {e}")
            return []

    @staticmethod
    def choose_calculation_category(
        tag: str, category: str | None = None
    ) -> str | None:
        for key, values in calculation_map.items():
            if category.lower() == category_map.get(key, "").lower():
                conditions = values
                break
        else:
            return

        for condition in conditions:
            for value in condition:
                if category_map.get(tag) and value.lower() == category_map[tag].lower():
                    return tag

    def choose_category(self, tag: str, category: str | None = None) -> str | None:
        if (
            category
            and category_map.get(tag)
            and category.lower() == category_map[tag].lower()
        ):
            return tag
        elif category:
            return self.choose_calculation_category(tag, category)
        elif settings.tags:
            for check_tag in settings.tags:
                if check_tag.lower() in tag.lower():
                    return tag
        else:
            return tag

    async def update_companies(self, ticker: str | None = None) -> None:
        try:
            ciks = await self.get_all_company_ciks(ticker)
            if not ciks:
                return
            logger.info(f"CIKs found for {len(ciks)} companies")

            saved_ciks = await self.db.get_company_ciks()
            new_ciks = list(set(ciks) - set(saved_ciks))

            save_task = None
            for i in range(0, len(new_ciks), settings.counter):
                fetch_start_time = time.time()
                tasks = [
                    self.get_company_submissions(cik=cik)
                    for cik in new_ciks[i : settings.counter + i]
                ]
                logger.info(
                    f"Fetching data for {len(new_ciks[i:settings.counter + i])} companies"
                )

                submissions_list = list(filter(None, await asyncio.gather(*tasks)))
                companies = list(
                    filter(
                        None,
                        [
                            self.extract_company_data(submissions)
                            for submissions in submissions_list
                        ],
                    )
                )
                logger.info(
                    f"Company data was fetched in {time.time() - fetch_start_time} seconds"
                )

                if save_task:
                    await save_task
                logger.info(
                    f"Saving data for {len(new_ciks[i:settings.counter + i])} companies"
                )
                save_task = asyncio.create_task(self.db.add_companies(companies))

            if save_task:
                await save_task
        except Exception as e:
            logger.error(f"Error updating companies: {e}")
        finally:
            logger.info("Finished updating companies")

    async def update_financial_statements(
        self, cik: str | None = None, category: str | None = None
    ) -> None:
        try:
            ciks = [cik] if cik else await self.db.get_company_ciks()
            for cik in ciks:
                facts = await self.get_company_facts(cik=cik)
                if not facts:
                    continue

                save_task = None
                for taxonomy, taxonomy_data in facts.items():
                    tasks = []
                    categories = []
                    fetch_start_time = time.time()
                    for tag, tag_data in taxonomy_data.items():
                        if not self.choose_category(tag, category):
                            continue

                        categories.append(
                            {
                                "tag": tag,
                                "category": (
                                    category_map[tag] if tag in category_map else tag
                                ),
                                "label": tag_data["label"],
                            }
                        )
                        tasks.append(
                            self.get_company_concept(
                                cik=cik, taxonomy=taxonomy, tag=tag
                            )
                        )
                    logger.info(
                        f"Fetching financial statements for company with "
                        f"CIK {cik}, taxonomy {taxonomy} and {len(tasks)} tags"
                    )
                    if save_task:
                        await save_task
                    save_task = asyncio.create_task(self.db.add_categories(categories))

                    concepts = list(filter(None, await asyncio.gather(*tasks)))
                    financial_statements = list(
                        filter(
                            None,
                            [
                                self.extract_financial_statements(concept)
                                for concept in concepts
                            ],
                        )
                    )
                    logger.info(
                        f"Financial statements was fetched in {time.time() - fetch_start_time} seconds"
                    )

                    if save_task:
                        await save_task
                    logger.info(
                        f"Saving financial statements for company with CIK {cik} "
                        f"and {len(financial_statements)} financial statements"
                    )
                    save_task = asyncio.create_task(
                        self.db.add_financial_statements(financial_statements)
                    )

                if save_task:
                    await save_task
        except Exception as e:
            logger.error(f"Error updating financial statements: {e}")
        finally:
            logger.info("Finished updating financial statements")

    async def start_companies_update(self, ticker: str | None = None) -> str:
        if (
            FinancialStatementService.companies_update_task
            and not FinancialStatementService.companies_update_task.done()
        ):
            return "Companies data is being updated"
        elif (
            FinancialStatementService.companies_update_task
            and FinancialStatementService.companies_update_task.done()
        ):
            await FinancialStatementService.companies_update_task

        FinancialStatementService.companies_update_task = asyncio.create_task(
            self.update_companies(ticker)
        )
        return "Company data has started to be updated"

    async def start_financial_statements_update(
        self, cik: str | None = None, category: str | None = None
    ) -> str:
        if (
            FinancialStatementService.financial_statements_update_task
            and not FinancialStatementService.financial_statements_update_task.done()
        ):
            return "Financial statements data is being updated"
        elif (
            self.financial_statements_update_task
            and FinancialStatementService.financial_statements_update_task.done()
        ):
            await FinancialStatementService.financial_statements_update_task

        FinancialStatementService.financial_statements_update_task = (
            asyncio.create_task(self.update_financial_statements(cik, category))
        )
        return "Financial statements data has started to be updated"
