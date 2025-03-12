from typing import Any

from loguru import logger
from sqlalchemy import select

from app.enums.base import OrderDirection
from app.models import Company
from app.models.category import FMPCategory
from app.models.financial_statement import FMPStatement
from app.repository.base import ModelType, SQLAlchemyRepository


class FinancialStatementRepository(SQLAlchemyRepository[FMPStatement]):
    model = FMPStatement
    join_load_list = [FMPStatement.company, FMPStatement.fmp_category]
    index_elements = [FMPStatement.period, FMPStatement.cik, FMPStatement.category_id]
    columns_to_update = [FMPStatement.value]

    async def get_one_or_none(
        self, order_by: str | None = None, order_direction: OrderDirection = OrderDirection.DESC, **filters: Any
    ) -> ModelType | None:
        """
        Get one object or None

        Args:
            order_by: order by
            order_direction: order direction

        Kwargs:
            filters: filters

        Returns:
            Object or None
        """
        logger.debug(f"Getting one or none of {self.model_name} with {order_by=}, {filters=}")

        where_clauses = []

        if ticker := filters.pop("ticker", None):
            where_clauses.append(Company.ticker.__eq__(ticker))

        if label := filters.pop("label", None):
            where_clauses.append(FMPCategory.label.ilike(label))

        where_clauses.extend(self.get_where_clauses(filters))

        statement = (
            select(self.model)
            .join(Company, FMPStatement.cik == Company.cik)
            .join(FMPCategory, FMPStatement.category_id == FMPCategory.id)
            .where(*where_clauses)
        )
        if order_by:
            statement = self.add_order_clause(statement, order_by, order_direction)

        return await self.execute(statement=statement, action=lambda result: result.unique().scalars().one_or_none())
