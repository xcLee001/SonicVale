from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sqlalchemy.orm import Session

from app.core.response import Res
from app.db.database import get_db
from app.dto.llm_provider_dto import LLMProviderCreateDTO, LLMProviderResponseDTO
from app.entity.llm_provider_entity import LLMProviderEntity
from app.services.llm_provider_service import LLMProviderService
from app.repositories.llm_provider_repository import LLMProviderRepository

# 初始化 router
router = APIRouter(prefix="/llm_providers", tags=["LLMProviders"])

# 依赖注入（实际LLM供应商可用 DI 容器）

def get_llm_service(db: Session = Depends(get_db)) -> LLMProviderService:
    repository = LLMProviderRepository(db)  # ✅ 传入 db
    return LLMProviderService(repository)




@router.post("/", response_model=Res[LLMProviderResponseDTO],
             summary="创建LLM供应商",
             description="根据LLM供应商信息创建LLM供应商，LLM供应商名称不可重复")
def create_llm_provider(dto: LLMProviderCreateDTO, service: LLMProviderService = Depends(get_llm_service)):
    """
    创建LLM供应商
    - dto: 前端 POST JSON 传入参数
    - service: Service 层注入
    """
    try:
        # DTO → Entity
        entity = LLMProviderEntity(**dto.__dict__)

        # 调用 Service 创建LLM供应商（返回 True/False）
        entityRes = service.create_llm_provider(entity)

        # 返回统一 Response
        if entityRes is not None:
            # 创建成功，可以返回 DTO 或者部分字段
            res = LLMProviderResponseDTO(**entityRes.__dict__)
            return Res(data=res, code=200, message="创建成功")
        else:
            return Res(data=None, code=400, message=f"LLM供应商 '{entity.name}' 已存在")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 按id查找
@router.get("/{llm_provider_id}", response_model=Res[LLMProviderResponseDTO],
            summary="查询LLM供应商",
            description="根据LLM供应商ID查询LLM供应商信息")
def get_llm_provider(llm_provider_id: int, service: LLMProviderService = Depends(get_llm_service)):
    entity = service.get_llm_provider(llm_provider_id)
    if entity:
        res = LLMProviderResponseDTO(**entity.__dict__)
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=None, code=404, message="LLM供应商不存在")

@router.get("/", response_model=Res[List[LLMProviderResponseDTO]],
            summary="查询所有LLM供应商",
            description="查询所有LLM供应商信息")
def get_all_llm_providers(service: LLMProviderService = Depends(get_llm_service)):
    entities = service.get_all_llm_providers()
    dtos = [LLMProviderResponseDTO(**e.__dict__) for e in entities]
    return Res(data=dtos, code=200, message="查询成功")


# ------------------- 修改LLM供应商 -------------------
@router.put("/{llm_provider_id}", response_model=Res[LLMProviderCreateDTO],
            summary="修改LLM供应商",
            description="根据LLM供应商ID修改LLM供应商信息")
def update_llm_provider(llm_provider_id: int, dto: LLMProviderCreateDTO, service: LLMProviderService = Depends(get_llm_service)):

    # 先根据id进行查找
    llm_provider = service.get_llm_provider(llm_provider_id)
    if not llm_provider:
        return Res(data=None, code=400, message="LLM供应商不存在")

    success = service.update_llm_provider(llm_provider_id,dto.dict(exclude_unset=True))
    if success:
        return Res(data=dto, code=200, message="更新成功")
    else:
        return Res(data=None, code=400, message="更新失败")


# ------------------- 删除LLM供应商 -------------------
@router.delete("/{llm_provider_id}", response_model=Res,
               summary="删除LLM供应商",
               description="根据LLM供应商ID删除LLM供应商,并且级联删除LLM供应商下所有章节以及内容")
def delete_llm_provider(llm_provider_id: int, service: LLMProviderService = Depends(get_llm_service)):
    success = service.delete_llm_provider(llm_provider_id)
    # todo 级联删除LLM供应商所有相关内容，比如LLM供应商下所有章节以及内容
    if success:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败或LLM供应商不存在")


# 测试供应商
@router.post("/test", response_model=Res)
def test_llm_provider(dto: LLMProviderCreateDTO, service: LLMProviderService = Depends(get_llm_service)):
    """
    测试供应商
    """
    entity = LLMProviderEntity(**dto.__dict__)
    res,msg = service.test_llm_provider(entity)
    if res == True:
        return Res(data=None, code=200, message="测试成功")
    else:
        return Res(data=None, code=400, message= msg)