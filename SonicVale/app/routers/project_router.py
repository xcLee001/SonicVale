import os
import shutil

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sqlalchemy.orm import Session

from app.core.config import getConfigPath
from app.core.response import Res
from app.db.database import get_db
from app.dto.project_dto import ProjectCreateDTO, ProjectResponseDTO, ProjectImportDTO
from app.entity.chapter_entity import ChapterEntity
from app.entity.project_entity import ProjectEntity
from app.models.po import ChapterPO
from app.repositories.chapter_repository import ChapterRepository
from app.repositories.line_repository import LineRepository
from app.repositories.llm_provider_repository import LLMProviderRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.tts_provider_repository import TTSProviderRepository
from app.services.chapter_service import ChapterService
from app.services.project_service import ProjectService
from app.repositories.project_repository import ProjectRepository
from app.services.role_service import RoleService

# 初始化 router
router = APIRouter(prefix="/projects", tags=["Projects"])

# 依赖注入（实际项目可用 DI 容器）

def get_service(db: Session = Depends(get_db)) -> ProjectService:
    repository = ProjectRepository(db)  # ✅ 传入 db
    return ProjectService(repository)

def get_chapter_service(db: Session = Depends(get_db)) -> ChapterService:
    repository = ChapterRepository(db)  # ✅ 传入 db
    return ChapterService(repository)

def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    repository = RoleRepository(db)  # ✅ 传入 db
    return RoleService(repository)


@router.post("/", response_model=Res[ProjectResponseDTO],
             summary="创建项目",
             description="根据项目信息创建项目，项目名称不可重复")
def create_project(dto: ProjectCreateDTO, service: ProjectService = Depends(get_service)):
    """
    创建项目
    - dto: 前端 POST JSON 传入参数
    - service: Service 层注入
    """
    try:
        # DTO → Entity
        entity = ProjectEntity(**dto.__dict__)

        # 调用 Service 创建项目（返回 True/False）
        entityRes,message = service.create_project(entity)

        # 返回统一 Response
        if entityRes is not None:
            # 创建成功，可以返回 DTO 或者部分字段
            res = ProjectResponseDTO(**entityRes.__dict__)
            return Res(data=res, code=200, message="创建成功")
        else:
            return Res(data=None, code=400, message=message)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 按id查找
@router.get("/{project_id}", response_model=Res[ProjectResponseDTO],
            summary="查询项目",
            description="根据项目ID查询项目信息")
def get_project(project_id: int, service: ProjectService = Depends(get_service)):
    entity = service.get_project(project_id)
    if entity:
        res = ProjectResponseDTO(**entity.__dict__)
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=None, code=404, message="项目不存在")

@router.get("/", response_model=Res[List[ProjectResponseDTO]],
            summary="查询所有项目",
            description="查询所有项目信息")
def get_all_projects(service: ProjectService = Depends(get_service)):
    entities = service.get_all_projects()
    dtos = [ProjectResponseDTO(**e.__dict__) for e in entities]
    return Res(data=dtos, code=200, message="查询成功")


# ------------------- 修改项目 -------------------
@router.put("/{project_id}", response_model=Res[ProjectCreateDTO],
            summary="修改项目",
            description="根据项目ID修改项目信息")
def update_project(project_id: int, dto: ProjectCreateDTO, service: ProjectService = Depends(get_service)):

    # 先根据id进行查找
    project = service.get_project(project_id)
    if not project:
        return Res(data=None, code=400, message="项目不存在")

    success = service.update_project(project_id,dto.dict())
    if success:
        return Res(data=dto, code=200, message="更新成功")
    else:
        return Res(data=None, code=400, message="更新失败")


# ------------------- 删除项目 -------------------
@router.delete("/{project_id}", response_model=Res,
               summary="删除项目",
               description="根据项目ID删除项目,并且级联删除项目下所有章节以及内容")
def delete_project(project_id: int, service: ProjectService = Depends(get_service), chapter_service: ChapterService = Depends(get_chapter_service),role_service: RoleService = Depends(get_role_service)):

    # 级联删除项目所有相关内容，比如项目下所有章节以及内容
    entities = chapter_service.get_all_chapters(project_id)
    for entity in entities:
        chapter_service.delete_chapter(entity.id)
    #     删除project目录
    project = service.get_project(project_id)

    project_path = os.path.join(project.project_root_path, str(project_id))
    if os.path.exists(project_path):
        shutil.rmtree(project_path)  # 删除整个文件夹及其所有内容
        print(f"已删除目录及内容: {project_path}")
    else:
        print(f"目录不存在: {project_path}")

    # 还要删除角色库中projet下的所有角色
    roles = role_service.get_all_roles(project_id)
    for role in roles:
        role_service.delete_role(role.id)
    success = service.delete_project(project_id)
    if success:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败或项目不存在")

# 直接导入整本小说内容，然后解析，创建章节
@router.post("/{project_id}/import")
def import_project(project_id: int, dto: ProjectImportDTO,service: ProjectService = Depends(get_service),
                   chapter_service: ChapterService = Depends(get_chapter_service)):

    content = dto.content
    # 删除该项目下的所有章节
    # chapters = chapter_service.get_all_chapters(project_id)
    # for chapter in chapters:
    #     chapter_service.delete_chapter(chapter.id)
    # 解析content
    chapter_contents = service.parse_content(content)
    if len(chapter_contents) == 0:
        return Res(code=400, message="导入失败")

    # 批量创建章节
    for chapter_content in chapter_contents:
        name = chapter_content["chapter_name"]
        content = chapter_content["content"]
        print("批量创建章节", name)
        chapter_service.create_chapter(ChapterEntity(project_id=project_id, title=name, text_content=content))
    return Res(code=200, message="导入成功")