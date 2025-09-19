from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class PromptCreateDTO(BaseModel):

    """业务实体：提示词"""
    name: str
    task: str
    description: Optional[str] = None
    content: Optional[str] = None
    id: Optional[int] = None


class PromptResponseDTO(BaseModel):

    """业务实体：提示词"""
    name: str
    task: str
    description: Optional[str] = None
    content: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None