import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.connection import get_db
from app.database.database import Database
from app.schemas.schemas import (
    CompaniesUpdateRequest,
    FinancialStatementsUpdateRequest,
    User,
)
from app.services.auth_service import get_current_user
from app.services.financial_statement_service import FinancialStatementService

router = APIRouter(prefix="/dev", tags=["Dev"])


@router.post("/update/companies")
async def start_companies_update(
    data: CompaniesUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    database = Database(session=db)
    parser = FinancialStatementService(db=database, user=current_user)
    return await parser.start_companies_update(data.ticker)


@router.post("/update/financial_statements")
async def start_financial_statements_update(
    data: FinancialStatementsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    database = Database(session=db)
    parser = FinancialStatementService(db=database, user=current_user)

    cik = None
    if data.ticker:
        cik = await parser.update_company_if_not_exists(data.ticker)
        if not cik:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company not found for stock ticker {data.ticker}",
            )

    return await parser.start_financial_statements_update(cik, data.category)


@router.get("/stop/companies")
async def stop_companies_update(current_user: User = Depends(get_current_user)):
    if not current_user.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    if not FinancialStatementService.companies_update_task:
        return "Companies are not updated."
    elif FinancialStatementService.companies_update_task.done():
        await FinancialStatementService.companies_update_task
        return "Update of companies is complete."
    else:
        FinancialStatementService.companies_update_task.cancel()
        return "Update of companies has stopped."


@router.get("/stop/financial_statements")
async def stop_financial_statements_update(
    current_user: User = Depends(get_current_user),
):
    if not current_user.superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    if not FinancialStatementService.financial_statements_update_task:
        return "Financial statements are not updated."
    elif FinancialStatementService.financial_statements_update_task.done():
        await FinancialStatementService.financial_statements_update_task
        return "Update of financial statements is complete."
    else:
        FinancialStatementService.financial_statements_update_task.cancel()
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied"
        )

    return {
        "companies_update": get_status(FinancialStatementService.companies_update_task),
        "financial_statements_update": get_status(
            FinancialStatementService.financial_statements_update_task
        ),
    }
