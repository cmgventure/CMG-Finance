import asyncio
import re
from functools import wraps

from fastapi import HTTPException, status
from loguru import logger

from app.schemas.financial_statement import FinancialStatementRequest


def synchronized_request(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        key = kwargs.pop("key", None)
        requests = getattr(self, "requests", None)

        if requests is None:
            logger.info(f"No requests in {self.__class__.__name__}")
        elif key in requests:
            logger.info(f"Waiting for {key}")
            await requests[key].wait()
            return None
        else:
            requests[key] = asyncio.Event()

        try:
            result = await func(self, *args, **kwargs)
        finally:
            if requests is not None and key in requests:
                logger.info(f"Releasing {key}")
                event = requests.pop(key)
                event.set()

        return result

    return wrapper


def get_task_status(task: asyncio.Task | None = None):
    if not task:
        return "Not started"
    elif task.done():
        return "Completed"
    elif task.cancelled():
        return "Cancelled"
    else:
        return "Running"


def parse_financial_statement_key(key: str) -> FinancialStatementRequest:
    try:
        # Split the key by '|'
        parts = key.split("|")
        if len(parts) < 2:
            raise ValueError(f"Invalid key format: {key}")
        elif len(parts) == 2:
            ticker, category = parts
            period = None
        else:
            ticker, category, period = parts

        return FinancialStatementRequest(ticker=ticker, category=category, period=period)
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
    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", category).split()
    words[0] = words[0].capitalize()
    return " ".join(words)
