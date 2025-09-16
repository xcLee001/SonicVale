from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class LLMProviderCreateDTO(BaseModel):
    """业务实体：LLM"""
    name: str
    id: Optional[int] = None
    api_base_url : Optional[str] = None
    api_key: Optional[str] = None
    model_list: Optional[str] = None
    status : Optional[int] = None

class LLMProviderResponseDTO(BaseModel):
    """业务实体：LLM"""
    name: str
    id: Optional[int] = None
    api_base_url : Optional[str] = None
    api_key: Optional[str] = None
    model_list: Optional[str] = None
    status : Optional[int] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None