from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import Res
from app.db.database import get_db
from app.dto.tts_provider_dto import TTSProviderResponseDTO
from app.dto.voice_dto import VoiceResponseDTO, VoiceCreateDTO
from app.entity.voice_entity import VoiceEntity
from app.repositories.multi_emotion_voice_repository import MultiEmotionVoiceRepository

from app.repositories.tts_provider_repository import TTSProviderRepository
from app.repositories.voice_repository import VoiceRepository

from app.services.tts_provider_service import TTSProviderService
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/voices", tags=["Voices"])


# 依赖注入（实际项目可用 DI 容器）

def get_voice_service(db: Session = Depends(get_db)) -> VoiceService:
    repository = VoiceRepository(db)
    multi_emotion_voice_repository = MultiEmotionVoiceRepository(db)
    return VoiceService(repository, multi_emotion_voice_repository)
def get_tts_provider_service(db: Session = Depends(get_db)) -> TTSProviderService:
    repository = TTSProviderRepository(db)
    return TTSProviderService(repository)
@router.post("", response_model=Res[VoiceResponseDTO],
             summary="创建音色",
             description="根据项目ID创建音色，音色名称在同一项目下不可重复" )
def create_voice(dto: VoiceCreateDTO, voice_service: VoiceService = Depends(get_voice_service),
                   tts_provider_service: TTSProviderService = Depends(get_tts_provider_service)):
    """创建音色"""
    try:
        # DTO → Entity
        entity = VoiceEntity(**dto.__dict__)
        # 判断tts_id是否存在
        tts_provider = tts_provider_service.get_tts_provider(dto.tts_provider_id)

        if tts_provider is None:
            return Res(data=None, code=400, message=f"tts服务提供商 '{dto.tts_provider_id}' 不存在")
        # 调用 Service 创建项目（返回 True/False）
        entityRes = voice_service.create_voice(entity)

        # 返回统一 Response
        if entityRes is not None:
            # 创建成功，可以返回 DTO 或者部分字段
            res = VoiceResponseDTO(**entityRes.__dict__)
            return Res(data=res, code=200, message="创建成功")
        else:
            return Res(data=None, code=400, message=f"音色 '{entity.name}' 已存在")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{voice_id}", response_model=Res[VoiceResponseDTO],
            summary="查询音色",
            description="根据音色id查询音色信息")
def get_voice(voice_id: int, voice_service: VoiceService = Depends(get_voice_service)):
    entity = voice_service.get_voice(voice_id)
    if entity:
        res = VoiceResponseDTO(**entity.__dict__)
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=None, code=404, message="项目不存在")

@router.get("/tts/{tts_provider_id}", response_model=Res[List[VoiceResponseDTO]],
            summary="查询tts供应商下的所有音色",
            description="根据tts供应商id,查询tts供应商下的所有音色信息")
def get_all_voices(tts_provider_id: int, voice_service: VoiceService = Depends(get_voice_service)):
    entities = voice_service.get_all_voices(tts_provider_id)
    if entities:
        res = [VoiceResponseDTO(**e.__dict__) for e in entities]
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=[], code=404, message="项目不存在音色")

# 修改，传入的参数是id
@router.put("/{voice_id}", response_model=Res[VoiceCreateDTO],
            summary="修改音色信息",
            description="根据音色id修改音色信息,并且不能修改项目id")
def update_voice(voice_id: int, dto: VoiceCreateDTO, voice_service: VoiceService = Depends(get_voice_service)):
    voice = voice_service.get_voice(voice_id)
    if voice is None:
        return Res(data=None, code=404, message="音色不存在")
    res = voice_service.update_voice(voice_id, dto.dict(exclude_unset=True))
    if res:
        return Res(data=dto, code=200, message="修改成功")
    else:
        return Res(data=None, code=400, message="修改失败")


# 根据id，删除
@router.delete("/{voice_id}", response_model=Res,
               summary="删除音色",
               description="根据音色id删除音色信息")
def delete_voice(voice_id: int, voice_service: VoiceService = Depends(get_voice_service)):
    success = voice_service.delete_voice(voice_id)
    if success:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败或音色不存在")


# tts_provider的查询和修改
# @router.get("/tts/provider/{tts_provider_id}", response_model=Res[TTSProviderResponseDTO])
# def get_tts_provider(tts_provider_id: int, tts_provider_service: TTSProviderService = Depends(get_tts_provider_service)):
#     tts_provider = tts_provider_service.get_tts_provider(tts_provider_id)
#     if tts_provider:
#         res = TTSProviderResponseDTO(**tts_provider.__dict__)
#         return Res(data=res, code=200, message="查询成功")
#     else:
#         return Res(data=None, code=404, message="tts服务提供商不存在")
#
# # tts_provider的修改
# @router.put("/tts/provider/{tts_provider_id}", response_model=Res[TTSProviderResponseDTO])
# def update_tts_provider(tts_provider_id: int, dto: TTSProviderResponseDTO, tts_provider_service: TTSProviderService = Depends(get_tts_provider_service)):
#     # 先判断是否存在
#     tts_provider = tts_provider_service.get_tts_provider(tts_provider_id)
#     if tts_provider is None:
#         return Res(data=None, code=404, message="tts服务提供商不存在")
#     tts_provider = tts_provider_service.update_tts_provider(tts_provider_id, dto.dict(exclude_unset=True))
#     if tts_provider:
#         return Res(data=None, code=200, message="修改成功")
#     else:
#         return Res(data=None, code=400, message="修改失败")

