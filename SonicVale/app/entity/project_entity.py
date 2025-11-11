
from dataclasses import dataclass
from datetime import datetime
from typing import Optional



@dataclass
class ProjectEntity:
    """业务实体：项目"""
    name: str
    id: Optional[int] = None
    description: Optional[str] = None
    llm_provider_id: Optional[int] = None
    llm_model: Optional[str] = None
    tts_provider_id: Optional[int] = None
    prompt_id: Optional[int] = None # 提示词
    # 精准填充
    is_precise_fill: Optional[int] = None
    # 项目保存地址
    project_root_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None





