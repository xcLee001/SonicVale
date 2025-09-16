# app/core/response.py
from pydantic.generics import GenericModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class Res(GenericModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
