
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# class MultiEmotionVoicePO(Base):
#     __tablename__ = "multi_emotion"
#     id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     emotion_id = Column(Integer, nullable=False)
#     voice_id = Column(Integer, nullable=False)
#     strength_id = Column(Integer, nullable=True)
#     reference_path = Column(String(255), nullable=True)
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
#     updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
#                         nullable=False)

@dataclass
class MultiEmotionVoiceEntity:
    """业务实体：多情感音色"""

    emotion_id: int
    voice_id: int
    strength_id: int
    id: Optional[int] = None
    reference_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

