from fastapi import HTTPException, status
from loguru import logger

from app.schemas.schemas import FinancialStatementRequest


def parse_financial_statement_key(key: str) -> FinancialStatementRequest:
    try:
        # Split the key by '|'
        parts = key.split("|")
        if len(parts) != 3:
            raise ValueError(f"Invalid key format: {key}")

        ticker, category, period = parts
        return FinancialStatementRequest(
            ticker=ticker.upper(), category=category, period=period
        )
    except Exception as e:
        logger.error(f"Failed to parse key: {key}. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse key: {key}",
        )
