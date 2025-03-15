from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.api.dependencies import fmp_service, get_current_user
from app.enums.fiscal_period import FiscalPeriodType
from app.utils.utils import get_task_status

router = APIRouter(prefix="/dev", tags=["Dev"])


@router.post("/update/companies")
async def start_companies_update(
    current_user: get_current_user, service: fmp_service, force_update: bool = False
) -> str:
    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    return await service.start_companies_update(force_update)


@router.post("/update/financial_statements")
async def start_financial_statements_update(
    current_user: get_current_user,
    service: fmp_service,
    periods: list[FiscalPeriodType],
    force_update: bool = False,
) -> str:
    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    return await service.start_financial_statements_update(periods, force_update)


@router.get("/stop/companies")
async def stop_companies_update(current_user: get_current_user, service: fmp_service) -> str:
    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    if not service.companies_update_task:
        return "Companies are not updated."
    elif service.companies_update_task.done():
        await service.companies_update_task
        return "Update of companies is complete."
    else:
        service.companies_update_task.cancel()
        return "Update of companies has stopped."


@router.get("/stop/financial_statements")
async def stop_financial_statements_update(current_user: get_current_user, service: fmp_service) -> str:
    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    if not service.financial_statements_update_task:
        return "Financial statements are not updated."
    elif service.financial_statements_update_task.done():
        await service.financial_statements_update_task
        return "Update of financial statements is complete."
    else:
        service.financial_statements_update_task.cancel()
        return "Update of financial statements has stopped."


@router.get("/check")
async def check_update_tasks(current_user: get_current_user, service: fmp_service) -> dict[str, str]:
    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    return {
        "companies_update": get_task_status(service.companies_update_task),
        "financial_statements_update": get_task_status(service.financial_statements_update_task),
    }
