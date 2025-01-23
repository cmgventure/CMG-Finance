import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection import get_db
from app.database.fmp_database import FMPDatabase
from app.schemas.schemas import User
from app.services.auth_service import get_current_user
from app.services.fmp import FMPService

router = APIRouter(prefix="/dev", tags=["Dev"])


@router.post("/update/companies")
async def start_companies_update(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    database = FMPDatabase(session=db)
    parser = FMPService(db=database)
    return await parser.start_companies_update()


@router.post("/update/financial_statements")
async def start_financial_statements_update(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    database = FMPDatabase(session=db)
    parser = FMPService(db=database)

    return await parser.start_financial_statements_update()


@router.get("/stop/companies")
async def stop_companies_update(current_user: User = Depends(get_current_user)):
    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    if not FMPService.companies_update_task:
        return "Companies are not updated."
    elif FMPService.companies_update_task.done():
        await FMPService.companies_update_task
        return "Update of companies is complete."
    else:
        FMPService.companies_update_task.cancel()
        return "Update of companies has stopped."


@router.get("/stop/financial_statements")
async def stop_financial_statements_update(
    current_user: User = Depends(get_current_user),
):
    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    if not FMPService.financial_statements_update_task:
        return "Financial statements are not updated."
    elif FMPService.financial_statements_update_task.done():
        await FMPService.financial_statements_update_task
        return "Update of financial statements is complete."
    else:
        FMPService.financial_statements_update_task.cancel()
        return "Update of financial statements has stopped."


@router.get("/check")
async def check_update_tasks(current_user: User = Depends(get_current_user)):
    def get_status(task: asyncio.Task):
        if not task:
            return "Not started"
        elif task.done():
            return "Completed"
        elif task.cancelled():
            return "Cancelled"
        else:
            return "Running"

    if not current_user.superuser:
        logger.error("Access Denied, user is not a superuser")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

    return {
        "companies_update": get_status(FMPService.companies_update_task),
        "financial_statements_update": get_status(FMPService.financial_statements_update_task),
    }
