from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import Res
from app.db.database import get_db
from app.dto.multi_emotion_voice_dto import MultiEmotionVoiceCreateDTO, MultiEmotionVoiceResponseDTO
from app.entity.multi_emotion_voice_entity import MultiEmotionVoiceEntity
from app.repositories.emotion_repository import EmotionRepository
from app.repositories.multi_emotion_voice_repository import MultiEmotionVoiceRepository
from app.repositories.strength_repository import StrengthRepository
from app.repositories.voice_repository import VoiceRepository
from app.services.emotion_service import EmotionService
from app.services.multi_emotion_voice_service import MultiEmotionVoiceService
from app.services.strength_service import StrengthService
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/multi_emotion_voices", tags=["MultiEmotionVoice"])

def get_multi_emotion_voice_service(db: Session = Depends(get_db)) -> MultiEmotionVoiceService:
    repository = MultiEmotionVoiceRepository(db)
    return MultiEmotionVoiceService(repository)
def get_voice_service(db: Session = Depends(get_db)) -> VoiceService:
    repository = VoiceRepository(db)
    multi_emotion_voice_repository = MultiEmotionVoiceRepository(db)
    return VoiceService(repository, multi_emotion_voice_repository)

def get_emotion_service(db: Session = Depends(get_db)) -> EmotionService:
    repository = EmotionRepository(db)
    return EmotionService(repository)

def get_strength_service(db: Session = Depends(get_db)) -> StrengthService:
    repository = StrengthRepository(db)
    return StrengthService(repository)

# 根据voice_id获取多音色
@router.get("/voice_id/{voice_id}", response_model=Res[List[MultiEmotionVoiceResponseDTO]],summary="根据voice_id获取多音色", description="根据voice_id获取多音色")
def get_multi_emotion_voice_by_voice_id(voice_id: int, multi_emotion_voice_service: MultiEmotionVoiceService = Depends(get_multi_emotion_voice_service),
                                        voice_service: VoiceService = Depends(get_voice_service)):
    # 应该查询voice
    voice = voice_service.get_voice(voice_id)
    if voice is None:
        return Res(code=404, message="音色不存在")
    entities = multi_emotion_voice_service.get_multi_emotion_voice_by_voice_id(voice_id)
    if entities is None:
        return Res(code=404, message="多音色不存在")
    else:
        res = [MultiEmotionVoiceResponseDTO(**entity.__dict__) for entity in entities]
        return Res(data=res, code=200, message="查询成功")

# 查询所有多音色
@router.get("", response_model=Res[List[MultiEmotionVoiceResponseDTO]],summary="查询所有多音色", description="查询所有多音色")
def get_all_multi_emotion_voice(multi_emotion_voice_service: MultiEmotionVoiceService = Depends(get_multi_emotion_voice_service)):
    entities = multi_emotion_voice_service.get_all_multi_emotion_voices()
    if not entities:
        return Res(data=[], code=200, message="查询成功")
    entities = [MultiEmotionVoiceResponseDTO(**e.__dict__) for e in entities]
    return Res(data=entities, code=200, message="查询成功")
# 创建
@router.post("", response_model=Res[MultiEmotionVoiceResponseDTO],summary="创建多情绪音色", description="创建多情绪音色")
def create_multi_emotion_voice(dto: MultiEmotionVoiceCreateDTO, multi_emotion_voice_service: MultiEmotionVoiceService = Depends(get_multi_emotion_voice_service),
                               voice_service: VoiceService = Depends(get_voice_service),
                               emotion_service: EmotionService = Depends(get_emotion_service),
                               strength_service: StrengthService = Depends(get_strength_service)):
    """创建多音色"""
    # 先要判断voice是否存在
    voice = voice_service.get_voice(dto.voice_id)
    # 判断情绪枚举是否存在
    emotion = emotion_service.get_emotion(dto.emotion_id)
    # 判断强度枚举是否存在
    strength = strength_service.get_strength(dto.strength_id)
    if voice is None or emotion is None or strength is None:
        return Res(code=500, message="创建失败,音色或者情绪枚举或者情绪强弱枚举不存在，不能创建多情绪音色")
    # DTO → Entity
    entity = MultiEmotionVoiceEntity(**dto.__dict__)
    entity = multi_emotion_voice_service.create_multi_emotion_voice(entity)
    if entity is None:
        return Res(code=500, message="创建失败,已存在多情绪音色")
    else :
        entity = MultiEmotionVoiceResponseDTO(**entity.__dict__)
        return Res(data=entity, code=200, message="创建成功")


# 修改
@router.put("/{multi_emotion_voice_id}", response_model=Res[MultiEmotionVoiceCreateDTO],summary="修改多情绪音色", description="修改多情绪音色")
def update_multi_emotion_voice(multi_emotion_voice_id: int, dto: MultiEmotionVoiceCreateDTO, multi_emotion_voice_service: MultiEmotionVoiceService = Depends(get_multi_emotion_voice_service)):
    """修改多音色"""
    entity = multi_emotion_voice_service.get_multi_emotion_voice_by_id(multi_emotion_voice_id)
    if entity is None:
        return Res(code=404, message="多音色不存在")
    res = multi_emotion_voice_service.update_multi_emotion_voice(multi_emotion_voice_id, dto.dict(exclude_unset=True))
    if res is None:
        return Res(code=500, message="修改失败")
    else:
        entityRes = MultiEmotionVoiceResponseDTO(**entity.__dict__)
        return Res(data=entityRes, code=200, message="修改成功")

# 删除
@router.delete("/{multi_emotion_voice_id}", response_model=Res[MultiEmotionVoiceResponseDTO],summary="删除多情绪音色", description="删除多情绪音色")
def delete_multi_emotion_voice(multi_emotion_voice_id: int, multi_emotion_voice_service: MultiEmotionVoiceService = Depends(get_multi_emotion_voice_service)):
    """删除多音色"""
    res = multi_emotion_voice_service.delete_multi_emotion_voice(multi_emotion_voice_id)
    if res:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败")

#
