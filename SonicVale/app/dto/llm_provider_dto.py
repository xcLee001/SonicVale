from dataclasses import Field
from datetime import datetime

from pydantic import BaseModel
from typing import Optional, Dict, Any


from pydantic import BaseModel, Field as PydField


class LLMProviderCreateDTO(BaseModel):
    """业务实体：LLM"""
    name: str
    id: Optional[int] = None
    api_base_url : Optional[str] = None
    api_key: Optional[str] = None
    model_list: Optional[str] = None
    status : Optional[int] = None

    # ✅ 默认自定义参数
    custom_params: Optional[str] = None


class LLMProviderResponseDTO(BaseModel):
    """业务实体：LLM"""
    name: str
    id: Optional[int] = None
    api_base_url : Optional[str] = None
    api_key: Optional[str] = None
    model_list: Optional[str] = None
    status : Optional[int] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # ✅ 默认自定义参数
    custom_params: Optional[str] = None