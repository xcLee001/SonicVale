from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class VoiceCreateDTO(BaseModel):
    name: str
    tts_provider_id: int
    id: Optional[int] = None
    reference_path: Optional[str] = None
    description: Optional[str] = None
    is_multi_emotion: Optional[int] = 0


class VoiceResponseDTO(BaseModel):
    name: str
    tts_provider_id: int
    id: Optional[int] = None
    reference_path : Optional[str] = None
    description : Optional[str] = None
    is_multi_emotion : Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VoiceExportDTO(BaseModel):
    """导出音色库请求DTO"""
    tts_provider_id: int
    export_path: str


class VoiceImportDTO(BaseModel):
    """导入音色库请求DTO"""
    tts_provider_id: int
    zip_path: str
    target_dir: str


class VoiceImportResultDTO(BaseModel):
    """导入音色库结果DTO"""
    success_count: int
    skipped_count: int
    skipped_names: List[str]

