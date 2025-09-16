from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import Res
from app.db.database import get_db
from app.dto.role_dto import RoleResponseDTO, RoleCreateDTO
from app.entity.role_entity import RoleEntity
from app.repositories.line_repository import LineRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.tts_provider_repository import TTSProviderRepository
from app.services.line_service import LineService
from app.services.project_service import ProjectService
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


# 依赖注入（实际项目可用 DI 容器）

def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    repository = RoleRepository(db)
    return RoleService(repository)
def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    repository = ProjectRepository(db)
    return ProjectService(repository)

def get_line_service(db: Session = Depends(get_db)) -> LineService:
    repository = LineRepository(db)
    role_repository = RoleRepository(db)
    tts_provider_repository = TTSProviderRepository(db)
    return LineService(repository,role_repository,tts_provider_repository)
@router.post("", response_model=Res[RoleResponseDTO],
             summary="创建角色",
             description="根据项目ID创建角色，角色名称在同一项目下不可重复" )
def create_role(dto: RoleCreateDTO, role_service: RoleService = Depends(get_role_service),
                   project_service: ProjectService = Depends(get_project_service)):
    """创建角色"""
    try:
        # DTO → Entity
        entity = RoleEntity(**dto.__dict__)
        # 判断project_id是否存在
        project = project_service.get_project(dto.project_id)
        if project is None:
            return Res(data=None, code=400, message=f"项目 '{dto.project_id}' 不存在")
        # 调用 Service 创建项目（返回 True/False）
        entityRes = role_service.create_role(entity)

        # 返回统一 Response
        if entityRes is not None:
            # 创建成功，可以返回 DTO 或者部分字段
            res = RoleResponseDTO(**entityRes.__dict__)
            return Res(data=res, code=200, message="创建成功")
        else:
            return Res(data=None, code=400, message=f"角色 '{entity.name}' 已存在")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{role_id}", response_model=Res[RoleResponseDTO],
            summary="查询角色",
            description="根据角色id查询角色信息")
def get_role(role_id: int, role_service: RoleService = Depends(get_role_service)):
    entity = role_service.get_role(role_id)
    if entity:
        res = RoleResponseDTO(**entity.__dict__)
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=None, code=404, message="项目不存在")

@router.get("/project/{project_id}", response_model=Res[List[RoleResponseDTO]],
            summary="查询项目下的所有角色",
            description="根据项目id查询项目下的所有角色信息")
def get_all_roles(project_id: int, role_service: RoleService = Depends(get_role_service)):
    entities = role_service.get_all_roles(project_id)
    if entities:
        res = [RoleResponseDTO(**e.__dict__) for e in entities]
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=[], code=404, message="项目不存在角色")

# 修改，传入的参数是id
@router.put("/{role_id}", response_model=Res[RoleCreateDTO],
            summary="修改角色信息",
            description="根据角色id修改角色信息,并且不能修改项目id")
def update_role(role_id: int, dto: RoleCreateDTO, role_service: RoleService = Depends(get_role_service)):
    role = role_service.get_role(role_id)
    if role is None:
        return Res(data=None, code=404, message="角色不存在")
    res = role_service.update_role(role_id, dto.dict(exclude_unset=True))
    if res:
        return Res(data=dto, code=200, message="修改成功")
    else:
        return Res(data=None, code=400, message="修改失败")


# 根据id，删除
@router.delete("/{role_id}", response_model=Res,
               summary="删除角色",
               description="根据角色id删除角色信息")
def delete_role(role_id: int, role_service: RoleService = Depends(get_role_service),line_service: LineService = Depends(get_line_service)):
    success = role_service.delete_role(role_id)
    if success:
        # 获取改角色下所有的台词
        line_service.clear_role_id(role_id)
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败或角色不存在")


# 根据内容进行解析

