from sqlalchemy import select

from app.models.company import Company
from app.repository.base import SQLAlchemyRepository


class CompanyRepository(SQLAlchemyRepository[Company]):
    model = Company

    async def get_tickers(self) -> list[str]:
        statement = select(self.model.ticker)
        return await self.execute(statement=statement, action=lambda result: result.scalars().all())
