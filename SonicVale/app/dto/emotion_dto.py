
from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class EmotionCreateDTO(BaseModel):
    name: str
    id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[int] = 1


class EmotionResponseDTO(BaseModel):
    name: str
    id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[int] = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


