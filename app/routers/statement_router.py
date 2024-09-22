import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection import get_db
from app.database.database import Database
from app.schemas.schemas import (
    FinancialStatementRequest,
    FinancialStatementsRequest,
    User,
)
from app.services.auth_service import get_current_user
from app.services.financial_statement_service import FinancialStatementService

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


@router.post("/financial_statement_bulk")
async def get_statements(
    data: FinancialStatementsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if not current_user.subscription and not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    logger.info(f"Accepted request with data keys: {data.payload}")
    logger.info(f"Accepted request with data length: {len(data.payload)}")
    start = time.time()

    database = Database(session=db)
    service = FinancialStatementService(db=database, user=current_user)

    tasks = [service.get_financial_statement_by_key(key) for key in data.payload]
    parsed_statements = await asyncio.gather(*tasks)

    logger.info(f"Parsed statements: {parsed_statements}")
    end = time.time()

    logger.info(f"TIME {end-start}. Return value for {len(data.payload)} statements")
    return {"parsed_statements": parsed_statements}
