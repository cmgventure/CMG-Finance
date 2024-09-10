from loguru import logger

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection import get_db
from app.database.database import Database
from app.schemas.schemas import FinancialStatementRequest, User
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

    logger.info(f"Accept request for {data.ticker} {data.category} {data.period}")

    database = Database(session=db)
    service = FinancialStatementService(db=database, user=current_user)
    financial_statement = await service.get_financial_statement(data)
    value = financial_statement.value if financial_statement else None

    logger.info(
        f"Return value for {data.ticker} {data.category} {data.period}: {value}"
    )
    return value
