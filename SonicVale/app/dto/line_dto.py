from datetime import datetime

from pydantic import BaseModel
from typing import Optional

class LineInitDTO(BaseModel):
    role_name: str
    text_content: str
    emotion_name: str
    strength_name: str


class LineOrderDTO(BaseModel):
    id: int
    line_order: int
class LineAudioProcessDTO(BaseModel):
    # 默认是1
    speed: Optional[float] = 1.0
    # 默认是1
    volume: Optional[float] = 1.0
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None

class LineCreateDTO(BaseModel):
    chapter_id: int
    role_id:Optional[int] = None
    voice_id : Optional[int] = None
    line_order: Optional[int] = None
    id: Optional[int] = None
    text_content: Optional[str] = None

    emotion_id: Optional[int] = None
    strength_id: Optional[int] = None

    audio_path : Optional[str] = None
    status : Optional[str] = None
    subtitle_path : Optional[str] = None

class LineResponseDTO(BaseModel):
    chapter_id: int
    role_id:Optional[int] = None
    voice_id : Optional[int] = None
    line_order: Optional[int] = None
    id: Optional[int] = None
    text_content: Optional[str] = None

    emotion_id: Optional[int] = None
    strength_id: Optional[int] = None

    audio_path : Optional[str] = None
    status : Optional[str] = None
    subtitle_path : Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


