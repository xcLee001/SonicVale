from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sqlalchemy.orm import Session

from app.core.enums import TaskEnum
from app.core.response import Res
from app.db.database import get_db
from app.dto.prompt_dto import PromptCreateDTO, PromptResponseDTO
from app.entity.prompt_entity import PromptEntity
from app.services.prompt_service import PromptService
from app.repositories.prompt_repository import PromptRepository

# 初始化 router
router = APIRouter(prefix="/prompts", tags=["Prompts"])

# 依赖注入（实际提示词可用 DI 容器）

def get_service(db: Session = Depends(get_db)) -> PromptService:
    repository = PromptRepository(db)  # ✅ 传入 db
    return PromptService(repository)




@router.post("/", response_model=Res[PromptResponseDTO],
             summary="创建提示词",
             description="根据提示词信息创建提示词，提示词名称不可重复")
def create_prompt(dto: PromptCreateDTO, service: PromptService = Depends(get_service)):
    """
    创建提示词
    - dto: 前端 POST JSON 传入参数
    - service: Service 层注入
    """
    try:
        # DTO → Entity
        entity = PromptEntity(**dto.__dict__)

        # 调用 Service 创建提示词（返回 True/False）
        entityRes = service.create_prompt(entity)

        # 返回统一 Response
        if entityRes is not None:
            # 创建成功，可以返回 DTO 或者部分字段
            res = PromptResponseDTO(**entityRes.__dict__)
            return Res(data=res, code=200, message="创建成功")
        else:
            return Res(data=None, code=400, message=f"创建失败,可能是不存在该任务或提示词数据不完整")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 按id查找
@router.get("/{prompt_id}", response_model=Res[PromptResponseDTO],
            summary="查询提示词",
            description="根据提示词ID查询提示词信息")
def get_prompt(prompt_id: int, service: PromptService = Depends(get_service)):
    entity = service.get_prompt(prompt_id)
    if entity:
        res = PromptResponseDTO(**entity.__dict__)
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=None, code=404, message="提示词不存在")

@router.get("/", response_model=Res[List[PromptResponseDTO]],
            summary="查询所有提示词",
            description="查询所有提示词信息")
def get_all_prompts(service: PromptService = Depends(get_service)):
    entities = service.get_all_prompts()
    dtos = [PromptResponseDTO(**e.__dict__) for e in entities]
    return Res(data=dtos, code=200, message="查询成功")


# ------------------- 修改提示词 -------------------
@router.put("/{prompt_id}", response_model=Res[PromptCreateDTO],
            summary="修改提示词",
            description="根据提示词ID修改提示词信息")
def update_prompt(prompt_id: int, dto: PromptCreateDTO, service: PromptService = Depends(get_service)):

    # 先根据id进行查找
    prompt = service.get_prompt(prompt_id)
    if not prompt:
        return Res(data=None, code=400, message="提示词不存在")

    success = service.update_prompt(prompt_id,dto.dict(exclude_unset=True))
    if success:
        return Res(data=dto, code=200, message="更新成功")
    else:
        return Res(data=None, code=400, message="更新失败,可能是不存在该任务或提示词数据不完整")


# ------------------- 删除提示词 -------------------
@router.delete("/{prompt_id}", response_model=Res,
               summary="删除提示词",
               description="根据提示词ID删除提示词,并且级联删除提示词下所有章节以及内容")
def delete_prompt(prompt_id: int, service: PromptService = Depends(get_service)):
    success = service.delete_prompt(prompt_id)
    # todo 级联删除提示词所有相关内容，比如提示词下所有章节以及内容
    if success:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败或提示词不存在")

# 获取所有的任务列表
@router.get("/tasks/all", response_model=Res[List[str]])
def get_all_tasks(service: PromptService = Depends(get_service)):
    tasks = service.get_all_tasks()
    return Res(data=tasks, code=200, message="查询成功")

# 根据任务列表获取对应的提示词
@router.get("/tasks/by", response_model=Res[List[PromptResponseDTO]])
def get_prompt_by_task(task: TaskEnum, service: PromptService = Depends(get_service)):
    prompts = service.get_prompt_by_task(task.value)  # 取枚举的值
    dtos = [PromptResponseDTO(**e.__dict__) for e in prompts]
    return Res(data=dtos, code=200, message="查询成功")



# 测试供应商
# @router.post("/test", response_model=Res)
# def test_prompt(dto: PromptCreateDTO, service: PromptService = Depends(get_service)):
#     """
#     测试供应商
#     """
#     entity = PromptEntity(**dto.__dict__)
#     success = service.test_prompt(entity)
#     if success:
#         return Res(data=None, code=200, message="测试成功")
#     else:
#         return Res(data=None, code=400, message="测试失败")