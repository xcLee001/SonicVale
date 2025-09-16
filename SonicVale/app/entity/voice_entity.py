
from dataclasses import dataclass
from datetime import datetime
from typing import Optional



@dataclass
class VoiceEntity:
    """业务实体：音色"""
    name: str
    tts_provider_id: int
    id: Optional[int] = None
    reference_path : Optional[str] = None
    description : Optional[str] = None
    is_multi_emotion : Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
