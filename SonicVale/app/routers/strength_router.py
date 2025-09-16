from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import Res
from app.db.database import get_db
from app.dto.strength_dto import StrengthResponseDTO, StrengthCreateDTO
from app.entity.strength_entity import StrengthEntity

from app.repositories.strength_repository import StrengthRepository

from app.services.strength_service import StrengthService

router = APIRouter(prefix="/strengths", tags=["Strengths"])


# 依赖注入（实际项目可用 DI 容器）

def get_strength_service(db: Session = Depends(get_db)) -> StrengthService:
    repository = StrengthRepository(db)
    return StrengthService(repository)

@router.post("", response_model=Res[StrengthResponseDTO],
             summary="创建情绪强弱枚举",
             description="根据项目ID创建情绪强弱枚举，情绪强弱枚举名称在同一项目下不可重复" )
def create_strength(dto: StrengthCreateDTO, strength_service: StrengthService = Depends(get_strength_service)):
    """创建情绪强弱枚举"""
    try:
        # DTO → Entity
        entity = StrengthEntity(**dto.__dict__)

        # 调用 Service 创建项目（返回 True/False）
        entityRes = strength_service.create_strength(entity)

        # 返回统一 Response
        if entityRes is not None:
            # 创建成功，可以返回 DTO 或者部分字段
            res = StrengthResponseDTO(**entityRes.__dict__)
            return Res(data=res, code=200, message="创建成功")
        else:
            return Res(data=None, code=400, message=f"情绪强弱枚举 '{entity.name}' 已存在")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{strength_id}", response_model=Res[StrengthResponseDTO],
            summary="查询情绪强弱枚举",
            description="根据情绪强弱枚举id查询情绪强弱枚举信息")
def get_strength(strength_id: int, strength_service: StrengthService = Depends(get_strength_service)):
    entity = strength_service.get_strength(strength_id)
    if entity:
        res = StrengthResponseDTO(**entity.__dict__)
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=None, code=404, message="情绪强弱枚举不存在")

@router.get("", response_model=Res[List[StrengthResponseDTO]],
            summary="查询所有情绪强弱枚举",
            description="根据所有情绪强弱枚举信息")
def get_all_strengths(strength_service: StrengthService = Depends(get_strength_service)):
    entities = strength_service.get_all_strengths()
    if entities:
        res = [StrengthResponseDTO(**e.__dict__) for e in entities]
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=[], code=404, message="项目不存在情绪强弱枚举")

# 修改，传入的参数是id
@router.put("/{strength_id}", response_model=Res[StrengthCreateDTO],
            summary="修改情绪强弱枚举信息",
            description="根据情绪强弱枚举id修改情绪强弱枚举信息,并且不能修改项目id")
def update_strength(strength_id: int, dto: StrengthCreateDTO, strength_service: StrengthService = Depends(get_strength_service)):
    strength = strength_service.get_strength(strength_id)
    if strength is None:
        return Res(data=None, code=404, message="情绪强弱枚举不存在")
    res = strength_service.update_strength(strength_id, dto.dict(exclude_unset=True))
    if res:
        return Res(data=dto, code=200, message="修改成功")
    else:
        return Res(data=None, code=400, message="修改失败，情绪强弱枚举名已存在")


# 根据id，删除，不开放
@router.delete("/{strength_id}", response_model=Res,
               summary="删除情绪强弱枚举",
               description="根据情绪强弱枚举id删除情绪强弱枚举信息")
def delete_strength(strength_id: int, strength_service: StrengthService = Depends(get_strength_service)):
    success = strength_service.delete_strength(strength_id)
    if success:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败或情绪强弱枚举不存在")



