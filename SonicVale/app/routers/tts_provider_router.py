from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sqlalchemy.orm import Session

from app.core.response import Res
from app.db.database import get_db
from app.dto.tts_provider_dto import TTSProviderCreateDTO, TTSProviderResponseDTO
from app.entity.tts_provider_entity import TTSProviderEntity
from app.services.tts_provider_service import TTSProviderService
from app.repositories.tts_provider_repository import TTSProviderRepository

# 初始化 router
router = APIRouter(prefix="/tts_providers", tags=["TTSProviders"])

# 依赖注入（实际TTS供应商可用 DI 容器）

def get_service(db: Session = Depends(get_db)) -> TTSProviderService:
    repository = TTSProviderRepository(db)  # ✅ 传入 db
    return TTSProviderService(repository)


# 按id查找
@router.get("/{tts_provider_id}", response_model=Res[TTSProviderResponseDTO],
            summary="查询TTS供应商",
            description="根据TTS供应商ID查询TTS供应商信息")
def get_tts_provider(tts_provider_id: int, service: TTSProviderService = Depends(get_service)):
    entity = service.get_tts_provider(tts_provider_id)
    if entity:
        res = TTSProviderResponseDTO(**entity.__dict__)
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=None, code=404, message="TTS供应商不存在")

@router.get("/", response_model=Res[List[TTSProviderResponseDTO]],
            summary="查询所有TTS供应商",
            description="查询所有TTS供应商信息")
def get_all_tts_providers(service: TTSProviderService = Depends(get_service)):
    entities = service.get_all_tts_providers()
    dtos = [TTSProviderResponseDTO(**e.__dict__) for e in entities]
    return Res(data=dtos, code=200, message="查询成功")


# ------------------- 修改TTS供应商 -------------------
@router.put("/{tts_provider_id}", response_model=Res[TTSProviderCreateDTO],
            summary="修改TTS供应商",
            description="根据TTS供应商ID修改TTS供应商信息")
def update_tts_provider(tts_provider_id: int, dto: TTSProviderCreateDTO, service: TTSProviderService = Depends(get_service)):

    # 先根据id进行查找
    tts_provider = service.get_tts_provider(tts_provider_id)
    if not tts_provider:
        return Res(data=None, code=400, message="TTS供应商不存在")

    success = service.update_tts_provider(tts_provider_id,dto.dict(exclude_unset=True))
    if success:
        return Res(data=dto, code=200, message="更新成功")
    else:
        return Res(data=None, code=400, message="更新失败")



# 测试tts是否正常
@router.post("/test", response_model=Res)
def test_tts_provider(dto: TTSProviderCreateDTO, service: TTSProviderService = Depends(get_service)):
    """
    测试tts是否正常
    """
    entity  = TTSProviderEntity(**dto.dict())
    success = service.test_tts_provider(entity)
    if success:
        return Res(data=None, code=200, message="测试成功")
    else:
        return Res(data=None, code=400, message="测试失败")



# ------------------- 删除TTS供应商 -------------------
# @router.delete("/{tts_provider_id}", response_model=Res,
#                summary="删除TTS供应商",
#                description="根据TTS供应商ID删除TTS供应商,并且级联删除TTS供应商下所有章节以及内容")
# def delete_tts_provider(tts_provider_id: int, service: TTSProviderService = Depends(get_service)):
#     success = service.delete_tts_provider(tts_provider_id)
#     # todo 级联删除TTS供应商所有相关内容，比如TTS供应商下所有章节以及内容
#     if success:
#         return Res(data=None, code=200, message="删除成功")
#     else:
#         return Res(data=None, code=400, message="删除失败或TTS供应商不存在")