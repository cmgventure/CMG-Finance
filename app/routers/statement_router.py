import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection import get_db, get_db_context, semaphore
from app.database.database import Database
from app.schemas.schemas import (
    FinancialStatementRequest,
    FinancialStatementsRequest,
    User,
)
from app.services.auth_service import get_current_user
from app.services.financial_statement_service import FinancialStatementService
from app.utils.utils import parse_financial_statement_key

router = APIRouter(tags=["Statements"])


@router.post("/financial_statement")
async def get_statement(
    data: FinancialStatementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> float | None:
    if not current_user.subscription and not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    logger.info(f"Accept request for {data.ticker} {data.category} {data.period}")
    start = time.time()

    database = Database(session=db)
    service = FinancialStatementService(db=database, user=current_user)
    financial_statement = await service.get_financial_statement(data)
    value = financial_statement.value if financial_statement else None

    end = time.time()
    logger.info(
        f"TIME {end-start}. Return value for {data.ticker} {data.category} {data.period}: {value}"
    )
    return value


async def get_financial_statement_task(user: User, key: str, force_update: bool) -> dict:
    async with semaphore:
        async with get_db_context() as db:
            database = Database(session=db)
            service = FinancialStatementService(db=database, user=user)
            # if force_update is True -> run API scrapper else get financial statement from DB
            if force_update:
                logger.warning(f"Force update for {key}")
                parsed_key = parse_financial_statement_key(key)
                cik = await service.update_company_if_not_exists(parsed_key.ticker)
                await service.update_financial_statements(cik, parsed_key.category)
            return await service.get_financial_statement_by_key(key)


@router.post("/financial_statement_bulk")
async def get_statements(
    data: FinancialStatementsRequest,
    current_user: User = Depends(get_current_user),
    force_update: bool = False,
) -> dict:
    if not current_user.subscription and not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    logger.info(f"Accepted request with data keys: {data.data}")
    logger.info(f"Accepted request with data length: {len(data.data)}")
    start = time.time()

    parsed_statements = {}

    tasks = [get_financial_statement_task(current_user, key, force_update) for key in data.data]
    for statement in await asyncio.gather(*tasks):
        parsed_statements.update(statement)

    logger.info(f"Parsed statements: {parsed_statements}")
    end = time.time()

    logger.info(f"TIME {end-start}. Return value for {len(data.data)} statements")
    return parsed_statements
