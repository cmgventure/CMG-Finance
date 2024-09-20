import time

from loguru import logger

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection import get_db
from app.database.database import Database
from app.schemas.schemas import FinancialStatementRequest, User, FinancialStatementsRequest, FinancialStatementResponse
from app.services.auth_service import get_current_user
from app.services.financial_statement_service import FinancialStatementService

router = APIRouter(tags=["Statements"])

requests = {}


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
    start = time.time()
    logger.info(f"Accept request for {data.ticker} {data.category} {data.period}")

    database = Database(session=db)
    service = FinancialStatementService(db=database, user=current_user)
    financial_statement = await service.get_financial_statement(data)
    value = financial_statement.value if financial_statement else None

    end = time.time()
    logger.info(
        f"TIME {end-start} .Return value for {data.ticker} {data.category} {data.period}: {value}"
    )
    return value

async def parse_financial_statement_key(key: str) -> FinancialStatementRequest:
    try:
        # Split the key by '|'
        parts = key.split('|')
        if len(parts) != 3:
            raise ValueError(f"Invalid key format: {key}")

        ticker, period, category = parts
        return FinancialStatementRequest(
            ticker=ticker,
            period=period,
            category=category
        )
    except Exception as e:
        logger.error(f"Failed to parse key: {key}. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse key: {key}"
        )


@router.post("/financial_statement_bulk")
async def get_statement(
        data: list[str],
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> dict:
    if not current_user.subscription and not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    logger.info(f"Accepted request with data keys: {data}")
    logger.info(f"Accepted request with data length: {len(data)}")
    start = time.time()

    parsed_statements: list[FinancialStatementResponse] = []

    database = Database(session=db)
    service = FinancialStatementService(db=database, user=current_user)

    for key in data:
        parsed_request = await parse_financial_statement_key(key)

        financial_statement = await database.get_financial_statement(
            parsed_request
        )

        value = financial_statement.value if financial_statement else None

        parsed_response = FinancialStatementResponse(
            ticker=parsed_request.ticker,
            period=parsed_request.period,
            category=parsed_request.category,
            value=value
        )

        parsed_statements.append(parsed_response)

    logger.info(f"Parsed statements: {parsed_statements}")
    end = time.time()

    logger.info(f"TIME {end-start} .Return value for {len(data)} statements")
    return {
        "parsed_statements": parsed_statements
    }
