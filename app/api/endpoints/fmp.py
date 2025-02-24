from fastapi import APIRouter, BackgroundTasks

from app.api.dependencies import fmp_service, get_current_user
from app.schemas.financial_statement import FinancialStatementRequest, FinancialStatementsRequest

router = APIRouter(prefix="/fmp", tags=["FMP"])


@router.post("/financial_statement")
async def get_statement(
    background_tasks: BackgroundTasks,
    current_user: get_current_user,
    service: fmp_service,
    data: FinancialStatementRequest,
    force_update: bool = False,
    wait_response: bool = False,
) -> float | None:
    return await service.get_financial_statement(
        background_tasks, data, force_update, wait_response, key=f"{data.ticker}|{data.period_type}"
    )


@router.post("/financial_statement/bulk")
async def get_statements(
    background_tasks: BackgroundTasks,
    current_user: get_current_user,
    service: fmp_service,
    data: FinancialStatementsRequest,
    force_update: bool = False,
    wait_response: bool = False,
) -> dict[str, float | None]:
    return await service.get_financial_statements(background_tasks, data, force_update, wait_response)
