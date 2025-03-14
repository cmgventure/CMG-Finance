from fastapi import APIRouter

from app.api.dependencies import fmp_service, get_current_user
from app.schemas.financial_statement import FinancialStatementRequest, FinancialStatementsRequest

router = APIRouter(prefix="/fmp", tags=["FMP"])


@router.post("/financial_statement")
async def get_statement(
    current_user: get_current_user,
    service: fmp_service,
    data: FinancialStatementRequest,
    force_update: bool = False,
    wait_response: bool = False,
) -> str | float | None:
    return await service.get_financial_statement(data, force_update, wait_response)


@router.post("/financial_statement/bulk")
async def get_statements(
    current_user: get_current_user,
    service: fmp_service,
    data: FinancialStatementsRequest,
    force_update: bool = False,
    wait_response: bool = False,
) -> dict[str, str | float | None]:
    return await service.get_financial_statements(data, force_update, wait_response)
