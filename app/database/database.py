import re
from datetime import datetime
from typing import Sequence

from loguru import logger
from sqlalchemy import and_, case, desc, distinct, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Category,
    Company,
    FinancialStatement,
    Subscription,
    User,
)
from app.schemas.schemas import FinancialStatementRequest


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
            await self.session.rollback()
            logger.error(f"Error adding subscription {subscription}: {e}")

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
            await self.session.rollback()
            logger.error(f"Error getting subscription by user id {user_id}: {e}")

    async def add_user(self, user: dict) -> None:
        try:
            stmt = insert(User).values(user).on_conflict_do_nothing()
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding user {user}: {e}")

    async def get_user(self, user_email: str) -> User | None:
        try:
            stmt = select(User).where(User.email == user_email)
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting subscription by user email {user_email}: {e}")

    async def add_company(self, company: dict) -> None:
        try:
            stmt = insert(Company).values(company).on_conflict_do_nothing()
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding company {company}: {e}")

    async def add_companies(self, companies: list[dict]) -> None:
        try:
            for company in companies:
                stmt = insert(Company).values(company).on_conflict_do_nothing()
                await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding companies {companies}: {e}")

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

    async def add_categories(self, categories: list):
        try:
            for category in categories:
                stmt = insert(Category).values(category).on_conflict_do_nothing()
                await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding categories: {e}")

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

    async def add_financial_statement(self, financial_statement: dict) -> None:
        try:
            stmt = (
                insert(FinancialStatement)
                .values(financial_statement)
                .on_conflict_do_nothing()
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding financial statement: {e}")

    async def add_financial_statements(self, financial_statements: list[dict]) -> None:
        try:
            for financial_statement in financial_statements:
                stmt = (
                    insert(FinancialStatement)
                    .values(financial_statement)
                    .on_conflict_do_nothing()
                )
                await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding financial statements: {e}")

    async def update_category_value(
        self, financial_statement: FinancialStatement
    ) -> FinancialStatement:
        categories = [
            {
                "tag": financial_statement.tag,
                "category": financial_statement.tag,
                "label": financial_statement.tag,
            }
        ]
        statement_dict = {
            col.name: getattr(financial_statement, col.name)
            for col in financial_statement.__table__.columns
        }

        await self.add_financial_statement(statement_dict)
        await self.add_categories(categories)

        return financial_statement

    async def find_financial_statement(
        self, ticker: str, category: str, period: str
    ) -> FinancialStatement | None:
        def category_case_expression(column):
            count_subquery = (
                select(func.count(distinct(column)))
                .join(FinancialStatement)
                .join(Company)
                .where(
                    Company.ticker == ticker,
                    FinancialStatement.period == period,
                    func.lower(column).like(f"%{category.lower()}%"),
                )
                .scalar_subquery()
            )

            return case(
                (count_subquery > 1, func.lower(column) == category.lower()),
                else_=func.lower(column).like(f"%{category.lower()}%"),
            )

        try:
            period = self.apply_fiscal_period_patterns(period)
            date = f"{period.split()[1]}-01-01"

            stmt = (
                select(FinancialStatement)
                .join(Company)
                .join(Category)
                .where(
                    and_(
                        Company.ticker == ticker,
                        FinancialStatement.period == period,
                        FinancialStatement.report_date >= date,
                        or_(
                            category_case_expression(Category.category),
                            category_case_expression(Category.tag),
                            category_case_expression(Category.label),
                        ),
                    )
                )
                .order_by(
                    desc(FinancialStatement.filing_date),
                    desc(FinancialStatement.report_date),
                )
            )

            result = await self.session.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error getting financial statement: {e}")
