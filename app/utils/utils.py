import re

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
        return FinancialStatementRequest(ticker=ticker.upper(), category=category, period=period)
    except Exception as e:
        logger.error(f"Failed to parse key: {key}. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse key: {key}",
        )


def apply_fiscal_period_patterns(period: str) -> str:
    patterns = [
        (r"^\d{4}$", r"FY \g<0>"),  # 2000 -> FY 2000
        (r"^(FY|Q\d)(\d{4})$", r"\1 \2"),  # Q12001 -> Q1 2001
        (r"^(FY|Q\d)\s*(\d{4})$", r"\1 \2"),  # Q2   2002 -> Q2 2002
        (r"^(\d{4})(FY|Q\d)$", r"\2 \1"),  # 2003Q3 -> Q3 2003
        (r"^(\d{4})\s*(FY|Q\d)$", r"\2 \1"),  # 2004   FY -> FY 2004
    ]

    for pattern, replacement in patterns:
        new_quarter = re.sub(pattern, replacement, period)
        if new_quarter != period:
            return new_quarter

    return period


def transform_category(category: str) -> str:
    words = re.sub(r"([A-Z])", r" \1", category).split()
    words[0] = words[0].capitalize()
    return " ".join(words)
