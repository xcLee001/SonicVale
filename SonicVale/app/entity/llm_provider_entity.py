
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class LLMProviderEntity:
    """业务实体：LLM"""
    name: str
    id: Optional[int] = None
    api_base_url : Optional[str] = None
    api_key: Optional[str] = None
    model_list : Optional[str] = None
    status : Optional[int] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # ✅ 自定义参数字段（默认值与数据库一致）
    custom_params: Optional[str] = None
