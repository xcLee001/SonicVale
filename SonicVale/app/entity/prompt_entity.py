
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# class PromptPO(Base):
#     __tablename__ = "prompt"
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     name = Column(String(255), nullable=False)
#     description = Column(Text, nullable=True)
#     content = Column(Text, nullable=True)
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
#     updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),nullable=False)

@dataclass
class PromptEntity:
    """业务实体：提示词"""
    name: str
    task: str
    description: Optional[str] = None
    content: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
