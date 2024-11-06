import re
from datetime import datetime
from typing import Sequence

from loguru import logger
from sqlalchemy import Result, asc, desc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Category,
    CategoryDefinitionType,
    Company,
    FinancialStatement,
    Subscription,
    User,
)
from app.schemas.schemas import (
    CategoryBaseSchema,
    CategorySchema,
    FinancialStatementSchema,
)


class Database:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_subscription(self, subscription: dict) -> None:
        try:
            stmt = (
                insert(Subscription)
                .values(subscription)
                .on_conflict_do_update(
                    index_elements=["id", "user_id"], set_=subscription
                )
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding subscription {subscription}: {e}")
            await self.session.rollback()

    async def get_subscription(self, user_id: str) -> Subscription | None:
        try:
            stmt = (
                select(Subscription)
                .join(User)
                .where(
                    Subscription.expired_at > datetime.utcnow(),
                )
                .order_by(desc(Subscription.created_at))
            )
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting subscription by user id {user_id}: {e}")
            await self.session.rollback()

    async def add_user(self, user: dict) -> None:
        try:
            stmt = insert(User).values(user).on_conflict_do_nothing()
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding user {user}: {e}")
            await self.session.rollback()

    async def get_user(self, user_email: str) -> User | None:
        try:
            stmt = select(User).where(User.email == user_email)
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting subscription by user email {user_email}: {e}")

    async def add_company(self, company: dict) -> None:
        try:
            stmt = (
                insert(Company)
                .values(company)
                .on_conflict_do_update(index_elements=["cik"], set_=company)
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding company {company}: {e}")
            await self.session.rollback()

    async def add_companies(self, companies: list[dict]) -> None:
        try:
            for company in companies:
                stmt = (
                    insert(Company)
                    .values(company)
                    .on_conflict_do_update(index_elements=["cik"], set_=company)
                )
                await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding companies {companies}: {e}")
            await self.session.rollback()

    async def get_company_cik(self, ticker: str) -> str | None:
        try:
            stmt = select(Company.cik).where(Company.ticker == ticker)
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting company cik by ticker {ticker}: {e}")

    async def get_company_ciks(self) -> Sequence | None:
        try:
            stmt = select(Company.cik)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting companies: {e}")

    async def add_categories(self, categories: list[CategoryBaseSchema]):
        try:
            for category in categories:
                stmt = (
                    insert(Category)
                    .values(category.model_dump())
                    .on_conflict_do_nothing()
                )
                await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding categories: {e}")
            await self.session.rollback()

    @staticmethod
    def apply_fiscal_period_patterns(period: str) -> str:
        patterns = [
            (r"^\d{4}$", r"FY \g<0>"),  # 2000 -> FY 2000
            (r"^(FY|Q\d)(\d{4})$", r"\1 \2"),  # Q12001 -> Q1 2001
            (r"^(FY|Q\d)\s*(\d{4})$", r"\1 \2"),  # Q2   2002 -> Q2 2002
            (r"^(\d{4})(FY|Q\d)$", r"\2 \1"),  # 2003Q3 -> Q3 2003
            (r"^(\d{4})\s*(FY|Q\d)$", r"\2 \1"),  # 2004   FY -> FY 2004
        ]

        for pattern, replacement in patterns:
            new_quarter = re.sub(pattern, replacement, period)
            if new_quarter != period:
                return new_quarter

        return period

    async def add_financial_statement(
        self, financial_statement: FinancialStatementSchema
    ) -> None:
        try:
            financial_statement = financial_statement.model_dump()
            stmt = (
                insert(FinancialStatement)
                .values(financial_statement)
                .on_conflict_do_update(
                    constraint="financial_statements_pkey",
                    set_={
                        "value": financial_statement["value"],
                        "form": financial_statement.get("form"),
                    },
                )
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding financial statement: {e}")
            await self.session.rollback()

    async def add_financial_statements(self, financial_statements: list[dict]) -> None:
        try:
            for financial_statement in financial_statements:
                stmt = (
                    insert(FinancialStatement)
                    .values(financial_statement)
                    .on_conflict_do_update(
                        constraint="financial_statements_pkey",
                        set_={
                            "value": financial_statement["value"],
                            "form": financial_statement.get("form"),
                        },
                    )
                )
                await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Error adding financial statements: {e}")
            await self.session.rollback()

    async def update_category_value(
        self, financial_statement: FinancialStatementSchema
    ) -> FinancialStatementSchema:
        try:
            await self.add_financial_statement(financial_statement)
        except Exception as e:
            logger.error(f"Error updating category value: {e}")
            await self.session.rollback()

        return financial_statement

    async def get_categories_for_label(
        self, category_label: str, only_formulas: bool = False
    ) -> list[CategorySchema]:
        stmt = (
            select(Category)
            .where(Category.label == category_label)
            .order_by(Category.priority)
        )

        if only_formulas:
            stmt = stmt.where(
                Category.type == CategoryDefinitionType.custom_formula.name
            )

        result = await self.session.execute(stmt)

        objects = result.scalars().all()

        if not objects:
            return []

        return [CategorySchema.model_validate(obj.__dict__) for obj in objects]

    async def _get_financial_statement_by_category_tag(
        self,
        ticker: str,
        category_label: str,
        period: str,
    ) -> Result:
        period = self.apply_fiscal_period_patterns(period)
        report_date = f"{period.split()[1]}-01-01"

        stmt = (
            select(FinancialStatement)
            .join(Company)
            .join(Category)
            .where(
                Company.ticker == ticker,
                FinancialStatement.period == period,
                FinancialStatement.report_date >= report_date,
                Category.label == category_label,
                FinancialStatement.value.isnot(None),
            )
            .order_by(
                asc(Category.priority),
                desc(FinancialStatement.filing_date),
                desc(FinancialStatement.report_date),
            )
        )

        return await self.session.execute(stmt)

    async def get_first_financial_statement_by_category_label(
        self,
        ticker: str,
        category_label: str,
        period: str,
    ) -> FinancialStatementSchema | None:
        result = await self._get_financial_statement_by_category_tag(
            ticker, category_label, period
        )
        obj = result.scalars().first()
        if obj:
            return FinancialStatementSchema.model_validate(obj)
        return None

    async def get_financial_statement_by_category_tag(
        self, ticker: str, value_definition_tag: str, period: str
    ) -> FinancialStatementSchema | None:
        period = self.apply_fiscal_period_patterns(period)
        report_date = f"{period.split()[1]}-01-01"

        stmt = (
            select(FinancialStatement)
            .join(Company)
            .join(Category)
            .where(
                Company.ticker == ticker,
                FinancialStatement.period == period,
                FinancialStatement.report_date >= report_date,
                Category.value_definition == value_definition_tag,
                FinancialStatement.value.isnot(None),
            )
            .order_by(
                asc(Category.priority),
                desc(FinancialStatement.filing_date),
                desc(FinancialStatement.report_date),
            )
        )
        result = await self.session.execute(stmt)
        obj = result.scalars().first()

        if obj:
            return FinancialStatementSchema.model_validate(obj)

        return None
