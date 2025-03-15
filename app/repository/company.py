from loguru import logger
from sqlalchemy import select

from app.models import FMPStatement
from app.models.company import Company, CompanyV2
from app.models.financial_statement import FMPStatementV2
from app.repository.base import SQLAlchemyRepository


class CompanyRepository(SQLAlchemyRepository[Company]):
    model = Company
    index_elements = [Company.cik]
    columns_to_update = [
        Company.sector,
        Company.industry,
        Company.market_cap,
        Company.pe,
        Company.price,
        Company.change,
        Company.volume,
    ]

    async def get_tickers(self) -> list[str]:
        logger.debug(f"Getting {self.model_name} tickers")

        statement = select(self.model.ticker)
        return await self.execute(statement=statement, action=lambda result: result.scalars().all())

    async def get_unfilled_companies(self) -> list[Company]:
        logger.debug(f"Getting {self.model_name} with unfilled financial statements")

        companies = await self.get_multi()

        statement = select(FMPStatement.cik).distinct()
        filled_companies = await self.execute(statement=statement, action=lambda result: result.scalars().all())

        return [company for company in companies if company.cik not in filled_companies]


class CompanyRepositoryV2(SQLAlchemyRepository[CompanyV2]):
    model = CompanyV2
    index_elements = [CompanyV2.cik, CompanyV2.ticker]
    columns_to_update = [
        CompanyV2.sector,
        CompanyV2.industry,
        CompanyV2.market_cap,
        CompanyV2.pe,
        CompanyV2.price,
        CompanyV2.change,
        CompanyV2.volume,
    ]

    async def get_tickers(self) -> list[str]:
        logger.debug(f"Getting {self.model_name} tickers")

        statement = select(self.model.ticker)
        return await self.execute(statement=statement, action=lambda result: result.scalars().all())

    async def get_unfilled_companies(self) -> list[CompanyV2]:
        logger.debug(f"Getting {self.model_name} with unfilled financial statements")

        companies = await self.get_multi()

        statement = select(FMPStatementV2.company_id).distinct()
        filled_companies = await self.execute(statement=statement, action=lambda result: result.scalars().all())

        return [company for company in companies if company.id not in filled_companies]
