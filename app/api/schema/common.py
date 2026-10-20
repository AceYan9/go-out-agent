# @Time: 2026/10/19 15:54
# @Author: yanggan

from typing import Generic, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")


class ApiResponse(GenericModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: T = None
