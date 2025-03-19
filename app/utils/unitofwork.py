from abc import ABC, abstractmethod
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import async_session
from app.repository.api_key import ApiKeyRepository
from app.repository.category import CategoryRepository
from app.repository.company import CompanyRepository, CompanyRepositoryV2
from app.repository.financial_statement import FinancialStatementRepository, FinancialStatementRepositoryV2
from app.repository.subscription import SubscriptionRepository
from app.repository.user import UserRepository


class ABCUnitOfWork(ABC):
    session: AsyncSession

    # Repository classes
    user: UserRepository
    api_key: ApiKeyRepository
    subscription: SubscriptionRepository
    company: CompanyRepository
    company_v2: CompanyRepositoryV2
    category: CategoryRepository
    financial_statement: FinancialStatementRepository
    financial_statement_v2: FinancialStatementRepositoryV2

    @abstractmethod
    def __init__(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, *args: Any) -> None:
        raise NotImplementedError


class UnitOfWork(ABCUnitOfWork):
    def __init__(self) -> None:
        self.session_maker = async_session

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self.session_maker()

        # Repository classes
        self.user = UserRepository(self.session)
        self.api_key = ApiKeyRepository(self.session)
        self.subscription = SubscriptionRepository(self.session)
        self.company = CompanyRepository(self.session)
        self.company_v2 = CompanyRepositoryV2(self.session)
        self.category = CategoryRepository(self.session)
        self.financial_statement = FinancialStatementRepository(self.session)
        self.financial_statement_v2 = FinancialStatementRepositoryV2(self.session)

        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc:
            logger.error(f"An error occurred while processing the request. Rolling back. Error: {repr(exc)}")
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
        await logger.complete()

        if exc:
            raise exc
