import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.core.connection import get_db_context, semaphore
from app.database.fmp_database import FMPDatabase
from app.schemas.schemas import FinancialStatementsRequest, User
from app.services.auth_service import get_current_user
from app.services.fmp import FMPService

router = APIRouter(tags=["FMP"])


async def get_financial_statement_task(key: str, force_update: bool = False, wait_response: bool = False) -> dict:
    async with semaphore:
        async with get_db_context() as db:
            database = FMPDatabase(session=db)
            service = FMPService(db=database)
            # if force_update is True -> run API scrapper else get financial statement from DB
            return await service.get_financial_statement_by_key(key, force_update, wait_response)


@router.post("/financial_statement/bulk")
async def get_statements(
    data: FinancialStatementsRequest,
    force_update: bool = False,
    wait_response: bool = False,
    current_user: User = Depends(get_current_user),
) -> dict:
    if not current_user.subscription and not current_user.superuser:
        logger.error(f"Access Denied, user {current_user.email} is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    logger.info(f"Accepted request with {len(data.keys)} keys: {data.keys}")

    parsed_statements = {}

    tasks = [get_financial_statement_task(key, force_update, wait_response) for key in data.keys]
    for statement in await asyncio.gather(*tasks):
        parsed_statements.update(statement)

    logger.info(f"Parsed {len(parsed_statements)} statements: {parsed_statements}")

    return parsed_statements
