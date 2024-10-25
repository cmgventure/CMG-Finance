import asyncio
import re
import time
from functools import wraps

import aiohttp
from aiohttp import ClientError
from fastapi import HTTPException
from loguru import logger
from sec_edgar_api import EdgarClient
from starlette import status

from app.core.config import settings
from app.database.database import Database
from app.database.models import (
    FinancialStatement,
    CategoryNew,
    CategoryDefinition,
    CategoryDefinitionType
)
from app.schemas.schemas import (
    FinancialStatementRequest,
    User,
    calculation_map,
    category_map,
)
from app.services.scheduler import scheduler_service
from app.utils.utils import parse_financial_statement_key


def synchronized_request(key_func):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            key = key_func(*args)
            requests = FinancialStatementService.requests

            if key in requests:
                logger.info(f"Waiting for {key}")
                await requests[key].wait()
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

    async def get_financial_statement(self, data: FinancialStatementRequest) -> FinancialStatement | None:
        # gets value from db or None
        financial_statement = await self.db.find_financial_statement(**data.model_dump())

        if financial_statement is not None:
            return financial_statement

        # at this point we didn't get the value for the category for the ticker because it is not in the db
        # we need to process multiple conditions on the category OR we need to scrape it?

        # run bg task to calculate value
        scheduler_service.add_job(
            self.task_collect_financial_statement_value,
            id=f"{data.ticker}|{data.category}",
            misfire_grace_time=None,
            trigger=settings.APSCHEDULER_JOB_TRIGGER,
            args=[data],
            **settings.APSCHEDULER_PROCESSING_TASK_TRIGGER_PARAMS,
        )

        return financial_statement

    async def get_financial_statement_by_key(self, key: str) -> dict:
        parsed_request = parse_financial_statement_key(key)

        financial_statement = await self.get_financial_statement(parsed_request)
        value = financial_statement.value if financial_statement else 0

        return {key: value}

    async def task_collect_financial_statement_value(self, data: FinancialStatementRequest) -> None:
        formula_namespace = {data.category}
        if await self.calculate_financial_statement(data, formula_namespace):
            return None

        cik = await self.update_company_if_not_exists(data.ticker)
        if not cik:
            logger.error(f"Company not found for stock ticker {data.ticker}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company not found for stock ticker {data.ticker}",
            )

        await self.update_financial_statements(cik=cik, category=data.category)

    async def get_category_value_by_definition(
        self,
        data: FinancialStatementRequest,
        category_definition: CategoryDefinition,
        formula_namespace: set[str]
    ) -> float | None:
        if category_definition.type == CategoryDefinitionType.tag and category_definition.tag_value:
            return (
                await self.db.find_financial_statement(
                    ticker=data.ticker,
                    category=category_definition.tag_value,
                    period=data.period
                )
            ).value

        if category_definition.type == CategoryDefinitionType.formula and category_definition.formula_value:
            # parse the formula string
            formula_operands = re.findall(r"\w+", category_definition.formula_value, re.IGNORECASE)
            formula_operators = re.findall(r"\(\+\)|\(\-\)", category_definition.formula_value, re.IGNORECASE)

            # get values for each operand
            formula_operands_values = []
            for category_operand in formula_operands:
                # check if the category is already in the namespace, if it is, it means we have a circular dependency

                # TODO: maybe formula_namespace should be a dict to store the values of the categories as well
                # so we can work with self-references in formulas like a = a + b

                if category_operand in formula_namespace:
                    return None

                # add the category to the namespace to prevent circular dependencies in formulas
                formula_namespace.add(category_operand)

                # get the value for the category
                await self.calculate_financial_statement(
                    data=FinancialStatementRequest(
                        ticker=data.ticker,
                        category=category_operand,
                        period=data.period,
                    ),
                    formula_namespace=formula_namespace
                )

            # if there are missing values, we can't calculate the formula correctly
            if not all(formula_operands_values):
                return None

            # convert operators to 1 or -1 for addition or subtraction respectively
            formula_converted_operators = [1 if operator_str == "(+)" else -1 for operator_str in formula_operators]

            # apply the operators to the operands
            for i in range(len(formula_converted_operators)):
                formula_operands_values[i + 1] *= formula_converted_operators[i]

            return sum(formula_operands_values)

        if category_definition.type == CategoryDefinitionType.exact and category_definition.exact_value:
            return category_definition.exact_value

    async def calculate_financial_statement(
        self,
        data: FinancialStatementRequest,
        formula_namespace: set[str]
    ) -> FinancialStatement | None:
        # 1. get category conditions (aka definitions)

        # the .definitions should be collected with subquery and ordered by priority
        category: CategoryNew | None = await self.db.get_category(data.category)

        # 2. iterate over definitions

        category_definition: CategoryDefinition
        for category_definition in category.definitions:
            value = await self.get_category_value_by_definition(data, category_definition, formula_namespace)

            if value is None:
                continue

            return await self.db.update_category_value(
                FinancialStatement(
                    ticker=data.ticker,
                    category=data.category,
                    period=data.period,
                    value=value,
                )
            )

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
                breakpoint()
                filings = submissions.get("filings", {}).get("recent", {})
                forms = filings.get("form", [])
                documents = filings.get("primaryDocument")
                for form, document in zip(forms, documents):
                    if form in ["10-Q", "10-K", "20-F"]:
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
                    if financial_statement["form"] not in ["10-Q", "10-K", "20-F"]:
                        continue

                    data = {
                        "cik": str(concept["cik"]).zfill(10),
                        "accession_number": financial_statement["accn"],
                        "period": f"{financial_statement['fp']} {financial_statement['fy']}",
                        "report_date": financial_statement["end"],
                        "filing_date": financial_statement["filed"],
                        "tag": concept["tag"],
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
