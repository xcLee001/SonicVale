from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class MultiEmotionVoiceCreateDTO(BaseModel):
    emotion_id: int
    voice_id: int
    strength_id: int
    id: Optional[int] = None
    reference_path: Optional[str] = None



class MultiEmotionVoiceResponseDTO(BaseModel):
    emotion_id: int
    voice_id: int
    strength_id: int
    id: Optional[int] = None
    reference_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

