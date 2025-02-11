from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.api.dependencies import fmp_service, get_current_user
from app.schemas.financial_statement import FinancialStatementsRequest

router = APIRouter(prefix="/fmp", tags=["FMP"])


@router.post("/financial_statement/bulk")
async def get_statements(
    current_user: get_current_user,
    service: fmp_service,
    data: FinancialStatementsRequest,
    force_update: bool = False,
    wait_response: bool = False,
) -> dict:
    if not current_user.subscription and not current_user.superuser:
        logger.error(f"Access Denied, user {current_user.email} is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    return await service.get_financial_statements(data, force_update, wait_response)
