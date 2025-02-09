from typing import Any

from sqlalchemy import asc, desc, select

from app.models.category import FMPCategory
from app.models.financial_statement import FMPStatement
from app.repository.base import SQLAlchemyRepository


class FinancialStatementRepository(SQLAlchemyRepository[FMPStatement]):
    model = FMPStatement
    join_load_list = [FMPStatement.company, FMPStatement.fmp_category]

    async def get_first_by_priority(self, **filters: Any) -> FMPStatement:
        """
        Get one object by priority

        Kwargs:
            filters: filters

        Returns:
            Object
        """

        statement = (
            select(self.model)
            .where(*self.get_where_clauses(filters))
            .order_by(asc(FMPCategory.priority), desc(self.model.filing_date), desc(self.model.report_date))
        )

        statement = self.add_loading_options(statement)
        return await self.execute(statement=statement, action=lambda result: result.unique().scalars().one_or_none())
