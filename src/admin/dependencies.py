from typing import Annotated
from fastapi import Depends
from src.core.dependencies import SessionDep
from src.admin.service import AdminService


def get_admin_service(session: SessionDep) -> AdminService:
    return AdminService(session)


AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
