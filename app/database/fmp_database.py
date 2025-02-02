from uuid import UUID, uuid4

from loguru import logger
from sqlalchemy import Result, asc, desc, func, select
from sqlalchemy.dialects.postgresql import insert

from app.database import Database
from app.database.models import Company, FMPCategory, FMPStatement
from app.schemas.fmp import FMPSchema
from app.schemas.schemas import CategoryDefinitionType, CategorySchema
from app.utils.utils import apply_fiscal_period_patterns, transform_category


class FMPDatabase(Database):
    async def get_categories_for_label(self, category_label: str, only_formulas: bool = False) -> list[CategorySchema]:
        try:
            stmt = (
                select(FMPCategory)
                .where(func.lower(FMPCategory.label).ilike(f"%{category_label.lower()}%"))
                .order_by(FMPCategory.priority)
            )

            result = await self.session.execute(stmt)

            objects = result.scalars().all()

            if not objects:
                return []

            return [CategorySchema.model_validate(obj.__dict__) for obj in objects]
        except Exception as e:
            logger.error(f"Error getting categories by label: {e}")
            await self.session.rollback()

    async def get_category_ids(self) -> dict[str, list[UUID]]:
        try:
            stmt = select(FMPCategory)

            result = await self.session.execute(stmt)

            objects = result.scalars().all()

            if not objects:
                return {}

            categories = {}
            for obj in objects:
                category = CategorySchema.model_validate(obj.__dict__)
                categories.setdefault(category.value_definition.lower(), []).append(category.id)

            return categories
        except Exception as e:
            logger.error(f"Error getting category ids: {e}")
            await self.session.rollback()

    async def _get_financial_statement_by_category_tag(
        self,
        ticker: str,
        category_label: str,
        period: str,
    ) -> Result:
        period = apply_fiscal_period_patterns(period)
        # report_date = f"{period.split()[1]}-01-01"

        stmt = (
            select(FMPStatement)
            .join(Company)
            .join(FMPCategory)
            .where(
                Company.ticker == ticker,
                func.lower(FMPStatement.period) == period.lower(),
                # FMPStatement.report_date >= report_date,
                func.lower(FMPCategory.label).ilike(f"%{category_label.lower()}%"),
                FMPStatement.value.isnot(None),
            )
            .order_by(
                asc(FMPCategory.priority),
                desc(FMPStatement.filing_date),
                desc(FMPStatement.report_date),
            )
        )

        return await self.session.execute(stmt)

    async def get_first_financial_statement_by_category_label(
        self,
        ticker: str,
        category_label: str,
        period: str,
    ) -> FMPSchema | None:
        result = await self._get_financial_statement_by_category_tag(ticker, category_label, period)
        obj = result.scalars().first()
        if obj:
            return FMPSchema.model_validate(obj)
        return None

    async def add_categories(self, financial_statements: list[dict]):
        try:
            categories = {}
            for financial_statement in financial_statements:
                category_key = financial_statement.pop("category", "")
                if financial_statement.get("category_id"):
                    continue
                elif category_id := categories.get(category_key):
                    financial_statement["category_id"] = category_id
                    continue

                category_id = uuid4()
                categories[category_key] = category_id
                financial_statement["category_id"] = category_id

                category = CategorySchema(
                    id=category_id,
                    label=transform_category(category_key),
                    value_definition=category_key,
                    description=category_key,
                    type=CategoryDefinitionType.api_tag,
                    priority=1,
                )

                stmt = insert(FMPCategory).values(category.model_dump()).on_conflict_do_nothing()
                await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding categories: {e}")
            await self.session.rollback()

    async def add_financial_statements(self, financial_statements: list[dict], update_categories: bool = False) -> None:
        try:
            if update_categories:
                await self.add_categories(financial_statements)

            for i in range(0, len(financial_statements), 5000):
                values = financial_statements[i : i + 5000]
                stmt = insert(FMPStatement).values(values)
                stmt = stmt.on_conflict_do_update(constraint="fmp_statements_pkey", set_={"value": stmt.excluded.value})
                await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding financial statements: {e}")
            await self.session.rollback()
