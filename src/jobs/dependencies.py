from typing import Annotated

from fastapi import Depends

from src.core.dependencies import SessionDep
from src.jobs.service import JobService


def get_job_service(session: SessionDep) -> JobService:
    return JobService(session)


JobServiceDep = Annotated[JobService, Depends(get_job_service)]
