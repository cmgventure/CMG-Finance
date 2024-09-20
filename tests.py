import asyncio
import time
from datetime import datetime, timedelta

from loguru import logger

from app.services.scheduler import scheduler_service


async def task1():
    await asyncio.sleep(20)
    logger.info("Task 1")

async def task2():
    await asyncio.sleep(2)
    logger.info("Task 2")

async def main():
    scheduler_service.start()
    key1 = "task1"
    key2 = "task2"
    trigger = "date"
    run_date = datetime.now() + timedelta(seconds=5)

    scheduler_service.add_job(
        task1,
        id=key1,
        trigger=trigger,
        run_date=run_date
    )

    time.sleep(5)

    scheduler_service.add_job(
        task2,
        id=key2,
        trigger=trigger,
        run_date=run_date
    )

if __name__ == '__main__':
    asyncio.run(main())
