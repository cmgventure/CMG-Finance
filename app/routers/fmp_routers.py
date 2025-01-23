import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.core.connection import get_db_context, semaphore
from app.database.fmp_database import FMPDatabase
from app.schemas.schemas import FinancialStatementsRequest, User
from app.services.auth_service import get_current_user
from app.services.fmp import FMPService

router = APIRouter(tags=["FMP"])


async def get_financial_statement_task(user: User, key: str, force_update: bool) -> dict:
    async with semaphore:
        async with get_db_context() as db:
            database = FMPDatabase(session=db)
            service = FMPService(db=database)
            # if force_update is True -> run API scrapper else get financial statement from DB
            return await service.get_financial_statement_by_key(key, force_update)


@router.post("/financial_statement_bulk")
async def get_statements(
    data: FinancialStatementsRequest,
    current_user: User = Depends(get_current_user),
    force_update: bool = False,
) -> dict:
    if not current_user.subscription and not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

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
