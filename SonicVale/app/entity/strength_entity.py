
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

    
@dataclass
class StrengthEntity:
    """业务实体：情绪强弱枚举"""
    name: str
    id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[int] = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
