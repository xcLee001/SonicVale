from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class VoiceCreateDTO(BaseModel):
    name: str
    tts_provider_id: int
    id: Optional[int] = None
    reference_path: Optional[str] = None
    description: Optional[str] = None
    is_multi_emotion: Optional[int] = 0


class VoiceResponseDTO(BaseModel):
    name: str
    tts_provider_id: int
    id: Optional[int] = None
    reference_path : Optional[str] = None
    description : Optional[str] = None
    is_multi_emotion : Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

