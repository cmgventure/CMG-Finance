from loguru import logger
from sqlalchemy import select

from app.models import FMPStatement
from app.models.company import Company
from app.repository.base import SQLAlchemyRepository


class CompanyRepository(SQLAlchemyRepository[Company]):
    model = Company

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
