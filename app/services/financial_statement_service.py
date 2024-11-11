import asyncio
import re
import time
from datetime import datetime
from functools import wraps
from itertools import groupby

import aiohttp
from aiohttp import ClientError
from dateutil.parser import parse
from fastapi import HTTPException
from loguru import logger
from sec_edgar_api import EdgarClient
from starlette import status

from app.core.config import settings
from app.database.database import Database
from app.database.models import CategoryDefinitionType
from app.schemas.schemas import (
    CategoryBaseSchema,
    CategorySchema,
    FinancialStatementRequest,
    FinancialStatementSchema,
    calculation_map,
    category_map,
    User
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
    semaphore = asyncio.Semaphore(settings.COUNTER)

    requests: dict = {}
    companies_update_task: asyncio.Task | None = None
    financial_statements_update_task: asyncio.Task | None = None

    def __init__(self, db: Database, user: User) -> None:
        self.db = db
        self.user_agent = user.email
        self.edgar_client = EdgarClient(user_agent=self.user_agent)

    async def get_financial_statement(
        self, data: FinancialStatementRequest, force_update: bool
    ) -> FinancialStatementSchema | None:
        # gets value from db or None
        if not force_update:
            financial_statement = (
                await self.db.get_first_financial_statement_by_category_label(
                    ticker=data.ticker, category_label=data.category, period=data.period
                )
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

    async def get_financial_statement_by_key(self, key: str, force_update: bool) -> dict:
        parsed_request = parse_financial_statement_key(key)

        financial_statement = await self.get_financial_statement(parsed_request, force_update)
        value = financial_statement.value if financial_statement else 0

        return {key: value}

    async def test_me(self, data: FinancialStatementRequest):
        formula_namespace = dict.fromkeys([data.category], None)
        return await self.calculate_financial_statement(data, formula_namespace)

    async def task_collect_financial_statement_value(
        self, data: FinancialStatementRequest
    ) -> None:
        formula_namespace = dict.fromkeys([data.category], None)

        if await self.calculate_financial_statement(
            data=data, formula_namespace=formula_namespace, only_formulas=True
        ):
            return None

        logger.info(f"Scraping data for {data.ticker} {data.category} {data.period}")

        cik = await self.update_company_if_not_exists(data.ticker)

        if not cik:
            logger.error(f"Company not found for stock ticker {data.ticker}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company not found for stock ticker {data.ticker}",
            )

        await self.update_financial_statements(cik=cik, label=data.category)

        logger.info(f"Data scraped for {data.ticker} {data.category} {data.period}")

    async def get_category_record_value(
        self,
        data: FinancialStatementRequest,
        category_record: CategorySchema,
        formula_namespace: dict[str, float | None],
    ) -> FinancialStatementSchema | None:
        # if it is a simple tag, we can get the value from the db
        if (
            category_record.type == CategoryDefinitionType.api_tag
            and category_record.value_definition
        ):
            # 1. what if there is not value by this tag ? -> returns None -> scrape data from the API
            return await self.db.get_financial_statement_by_category_tag(
                ticker=data.ticker,
                value_definition_tag=category_record.value_definition,
                period=data.period,
            )

        # if it is a formula, we need to calculate the value of it by parsing the formula
        # and getting the values of each the operands separately
        elif (
            category_record.type == CategoryDefinitionType.custom_formula
            and category_record.value_definition
        ):
            # parse the formula string, extract operands and operators from the formula string
            formula_operands = re.findall(
                settings.CUSTOM_FORMULA_OPERAND_PATTERN, category_record.value_definition, re.IGNORECASE
            )
            formula_operators = re.findall(
                settings.CUSTOM_FORMULA_OPERATOR_PATTERN, category_record.value_definition, re.IGNORECASE
            )

            # get values for each operand - human-readable category titles
            financial_statements = []
            for formula_operand in formula_operands:
                # check if the category is already in the namespace, if it is, it means we have a circular dependency
                if formula_operand in formula_namespace:
                    return formula_namespace[formula_operand]

                # add the category to the namespace to prevent circular dependencies in formulas
                formula_namespace[formula_operand] = None

                formula_operand_financial_statement = (
                    await self.calculate_financial_statement(
                        data=FinancialStatementRequest(
                            ticker=data.ticker,
                            period=data.period,
                            category=formula_operand,
                        ),
                        formula_namespace=formula_namespace,
                    )
                )

                financial_statements.append(formula_operand_financial_statement)

                formula_namespace[formula_operand] = formula_operand_financial_statement

            # if there are missing values, we can't calculate the formula correctly
            if not all(financial_statements) or not all(
                [fs.value for fs in financial_statements if fs is not None]
            ):
                logger.error(
                    f"Missing values. Unable to calculate value for category definition {category_record}"
                )
                return None

            # convert operators to 1 or -1 for addition or subtraction respectively
            formula_converted_operators = [
                1 if operator_str == "(+)" else -1 for operator_str in formula_operators
            ]

            # apply the operators to the operands
            for i in range(len(formula_converted_operators)):
                financial_statements[i + 1].value *= formula_converted_operators[i]

            value = sum(
                [
                    financial_statement.value
                    for financial_statement in financial_statements
                ]
            )

            # We have to return a new FinancialStatement object with the calculated value.
            # For this, we will take the first financial statement object and update its value,
            # then return it, since it has all the necessary values for fields.
            financial_statement = financial_statements[0]
            financial_statement.value = value
            financial_statement.category_id = category_record.id

            return financial_statement

        # if it is an exact value, we can just return it
        elif (
            category_record.type == CategoryDefinitionType.exact_value
            and category_record.value_definition
        ):
            raise NotImplementedError("Exact value type is not implemented yet")

        else:
            logger.error(
                f"Unable to calculate value for category definition {category_record}"
            )
            return None

    async def calculate_financial_statement(
        self,
        data: FinancialStatementRequest,
        formula_namespace: dict[str, None],
        only_formulas: bool = False,
    ) -> FinancialStatementSchema | None:
        # 1. get category metadata from the db

        categories: list[CategorySchema]
        categories = await self.db.get_categories_for_label(
            category_label=data.category, only_formulas=only_formulas
        )

        logger.debug(
            f"Found {len(categories)} categories for tag '{data.category}' ({only_formulas=})"
        )

        if not categories:
            logger.error(f"Category not found for tag {data.category}")
            # if None - scrape data from the API
            return None

        # 2. iterate over definitions

        for category_record in categories:
            financial_statement: FinancialStatementSchema | None = (
                await self.get_category_record_value(
                    data=data,  # maybe change data.category to category_record.label
                    category_record=category_record,
                    formula_namespace=formula_namespace,
                )
            )

            if financial_statement is None:
                continue

            return await self.db.update_category_value(financial_statement)

        logger.error(
            f"Unable to calculate value for any formula for category {data.category}"
        )

        return None

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

    async def get_company_concept(self, cik: str, taxonomy: str, tag: str) -> dict | None:
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
    def filter_units(units: list[dict]) -> list[dict]:
        def get_group_key(item) -> tuple:
            grouping_keys = ["accn", "form", "fp", "fy", "filed"]
            return tuple(item[key] for key in grouping_keys)

        def filter_date(date: str) -> datetime | None:
            if not date:
                return
            return parse(date)

        filtered_data = []
        for _, group in groupby(units, key=get_group_key):
            group_list = list(group)

            selected = max(
                group_list,
                key=lambda x: (
                    filter_date(x.get("end", "")),
                    filter_date(x.get("start", "")),
                ),
            )
            filtered_data.append(selected)

        return filtered_data

    @staticmethod
    def extract_company_data(submissions: dict) -> dict | None:
        try:
            ticker = None
            if not submissions["tickers"]:
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

    def extract_financial_statements(self, concept: dict, category_id: str) -> list:
        try:
            financial_statements = []
            for units in concept.get("units", {}).values():
                filtered_units = self.filter_units(units)
                for financial_statement in filtered_units:
                    if financial_statement["form"] not in ["10-Q", "10-K", "20-F"]:
                        continue
                    # filter by max("start" and "end") dates

                    data = {
                        "cik": str(concept["cik"]).zfill(10),
                        "accession_number": financial_statement["accn"],
                        "period": f"{financial_statement['fp']} {financial_statement['fy']}",
                        "report_date": financial_statement["end"],
                        "filing_date": financial_statement["filed"],
                        "form": financial_statement["form"],
                        "value": financial_statement["val"],
                        "category_id": category_id,
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
                tasks = [
                    self.get_company_submissions(cik=cik)
                    for cik in new_ciks[i : settings.COUNTER + i]
                ]
                logger.info(
                    f"Fetching data for {len(new_ciks[i:settings.COUNTER + i])} companies"
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
                    f"Saving data for {len(new_ciks[i:settings.COUNTER + i])} companies"
                )
                save_task = asyncio.create_task(self.db.add_companies(companies))

            if save_task:
                await save_task
        except Exception as e:
            logger.error(f"Error updating companies: {e}")
        finally:
            logger.info("Finished updating companies")

    async def fill_financial_statements(self):
        try:
            ciks = await self.db.get_company_ciks()
            for cik in ciks:
                facts = await self.get_company_facts(cik=cik)
                if not facts:
                    continue

                save_task = None
                for taxonomy, taxonomy_data in facts.items():
                    tasks = []
                    categories = []
                    for tag, tag_data in taxonomy_data.items():
                        if not tag_data.get("description"):
                            tag_data["description"] = ""
                        categories.append(
                            CategoryBaseSchema(
                                label=re.sub(r"(?<!^)(?=[A-Z])", " ", tag),
                                value_definition=tag,
                                description=tag_data.get("description", ""),
                                type=CategoryDefinitionType.api_tag,
                                priority=1,
                            )
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
                    # if save_task:
                    #     await save_task
                    # save_task = asyncio.create_task(self.db.add_categories(categories))

                    concepts = list(filter(None, await asyncio.gather(*tasks)))
                    financial_statements = list(
                        filter(
                            None,
                            [
                                self.extract_financial_statements(concept, "")
                                for concept in concepts
                            ],
                        )
                    )
        except Exception as e:
            logger.error(str(e))

    async def update_financial_statements(self, cik: str, label: str) -> None:
        try:
            facts = await self.get_company_facts(cik=cik)

            if not facts:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No facts for category label",
                )

            custom_formula_operands = []

            categories = await self.db.get_categories_for_label(label)

            for category in categories:
                if category.type == CategoryDefinitionType.custom_formula:
                    formula_operands = re.findall(
                        pattern=settings.CUSTOM_FORMULA_OPERAND_PATTERN,
                        string=category.value_definition,
                        flags=re.IGNORECASE
                    )
                    custom_formula_operands.extend(formula_operands)
                    continue

            for taxonomy, taxonomy_data in facts.items():
                fetch_start_time = time.time()

                for category in categories:

                    if not taxonomy_data.get(category.value_definition):
                        continue

                    concept = await self.get_company_concept(cik=cik, taxonomy=taxonomy, tag=category.value_definition)
                    financial_statements = list(
                        filter(
                            None,
                            self.extract_financial_statements(
                                concept, str(category.id)
                            ),
                        )
                    )
                    logger.info(
                        f"Financial statements was fetched in {time.time() - fetch_start_time} seconds"
                    )
                    logger.info(
                        f"Saving financial statements for company with CIK {cik} "
                        f"and {len(financial_statements)} financial statements"
                    )
                    await self.db.add_financial_statements(financial_statements)

            custom_formula_operands = list(set(custom_formula_operands))
            if custom_formula_operands:
                for operand in custom_formula_operands:
                    await self.update_financial_statements(cik=cik, label=operand)

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

    async def start_financial_statements_update(self) -> str:
        if (
            FinancialStatementService.financial_statements_update_task
            and not FinancialStatementService.financial_statements_update_task.done()
        ):
            return "Financial statements data is being updated"
        elif (
            FinancialStatementService.financial_statements_update_task
            and FinancialStatementService.financial_statements_update_task.done()
        ):
            await FinancialStatementService.financial_statements_update_task

        FinancialStatementService.financial_statements_update_task = (
            asyncio.create_task(self.fill_financial_statements())
        )
        return "Financial statements data has started to be updated"
