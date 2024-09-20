from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.core.config import settings


class SchedulerService:
    PING_TASK_ID = "ping_task"

    # these tasks are required and should not be removed
    REQUIRED_TASK_IDS = [
        PING_TASK_ID,
    ]

    def __init__(self, scheduler_cls):
        self.scheduler = scheduler_cls()
        logger.info(f"Created a scheduler: {self.scheduler}")
        self.add_ping_task()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    # utility methods

    def add_ping_task(self):
        self.scheduler.add_job(
            self.ping,
            id="ping_task",
            trigger="interval",
            seconds=60,
            misfire_grace_time=None,
        )

    def ping(self):
        is_running = self.scheduler.running
        logger.info(f"Scheduler is running: {is_running}")
        return is_running

    # apscheduler API

    def modify_job(self, job_id, **changes):
        self.scheduler.modify_job(job_id, **changes)
        logger.info(f"Modified a job {job_id} in a scheduler: {self.scheduler}")

    def add_job(self, func, *args, **kwargs):
        job_id = kwargs.get("id")
        if job := self.get_job(job_id):
            logger.warning(
                f"Unable to add a job {job_id} from a scheduler: {self.scheduler}. Job already exists."
            )
            return job
        job = self.scheduler.add_job(func, *args, **kwargs)
        logger.info(
            f"Added a job {job} to a scheduler: {self.scheduler}, args: {args}, kwargs: {kwargs}"
        )
        return job

    def remove_job(self, job_id):
        if not self.get_job(job_id):
            logger.warning(
                f"Unable to remove a job {job_id} from a scheduler: {self.scheduler}. Job not found."
            )
            return
        self.scheduler.remove_job(job_id)
        logger.info(f"Removed a job {job_id} from a scheduler: {self.scheduler}")

    def reschedule_job(self, job_id, trigger, **trigger_params):
        self.scheduler.reschedule_job(job_id, trigger, **trigger_params)
        logger.info(f"Rescheduled a job {job_id} in a scheduler: {self.scheduler}")

    def get_jobs(self):
        return self.scheduler.get_jobs()

    def get_job(self, job_id):
        return self.scheduler.get_job(job_id)

    def shutdown(self):
        self.scheduler.shutdown()
        logger.info(f"Shut down a scheduler: {self.scheduler}")
        self.print_jobs()

    def start(self):
        self.scheduler.start()
        logger.info(f"Started a scheduler: {self.scheduler}")

    def print_jobs(self):
        self.scheduler.print_jobs()

    def add_listener(self, listener, mask=None):
        if mask is None:
            self.scheduler.add_listener(
                listener
            )  # default mask is EVENT_ALL - all events
        else:
            self.scheduler.add_listener(listener, mask)
        logger.info(
            f"Added a listener {listener} with mask {mask} to a scheduler: {self.scheduler}"
        )


scheduler_service = SchedulerService(AsyncIOScheduler)
