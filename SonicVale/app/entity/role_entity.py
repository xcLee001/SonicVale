
from dataclasses import dataclass
from datetime import datetime
from typing import Optional



@dataclass
class RoleEntity:
    """业务实体：角色"""
    name: str
    project_id: int
    id: Optional[int] = None
    default_voice_id : Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

