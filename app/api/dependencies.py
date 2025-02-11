from typing import Annotated

from fastapi import Depends

from app.schemas.user import User
from app.services.auth import AuthService
from app.services.category import CategoryService
from app.services.fmp import FMPService
from app.services.squarespace import SquarespaceService
from app.utils.unitofwork import ABCUnitOfWork, UnitOfWork

UnitOfWorkDep = Annotated[ABCUnitOfWork, Depends(UnitOfWork)]

get_current_user = Annotated[User, Depends(AuthService.get_current_user)]
# get_superuser = Annotated[User, Depends(AuthService.get_superuser)]

auth_service = Annotated[AuthService, Depends(AuthService)]
category_service = Annotated[CategoryService, Depends(CategoryService)]
fmp_service = Annotated[FMPService, Depends(FMPService)]
squarespace_service = Annotated[SquarespaceService, Depends(SquarespaceService)]
