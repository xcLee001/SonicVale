from sqlalchemy import Sequence

from app.entity.project_entity import ProjectEntity
from app.models.po import ProjectPO

from app.repositories.project_repository import ProjectRepository


class ProjectService:

    def __init__(self, repository: ProjectRepository):
        """注入 repository"""
        self.repository = repository

    def create_project(self,  entity: ProjectEntity):
        """创建新项目
        - 检查同名项目是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """
        project = self.repository.get_by_name(entity.name)
        if project:
            return None
        # 手动将entity转化为po
        po = ProjectPO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = ProjectEntity(**data)

        # 将po转化为entity
        return entity


    def get_project(self, project_id: int) -> ProjectEntity | None:
        """根据 ID 查询项目"""
        po = self.repository.get_by_id(project_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = ProjectEntity(**data)
        return res

    def get_all_projects(self) -> Sequence[ProjectEntity]:
        """获取所有项目列表"""
        pos = self.repository.get_all()
        # pos -> entities

        entities = [
            ProjectEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_project(self, project_id: int, data:dict) -> bool:
        """更新项目
        - 可以只更新部分字段
        - 检查同名冲突
        """
        name = data["name"]
        if self.repository.get_by_name(name) and self.repository.get_by_name(name).id != project_id:
            return False
        self.repository.update(project_id, data)
        return True

    def delete_project(self, project_id: int) -> bool:
        """删除项目
        - 可以添加业务校验，例如项目下有章节是否允许删除
        - 后续需要级联删除所有章节内容
        """
        res = self.repository.delete(project_id)
        return res


    def search_projects(self, keyword: str) -> Sequence[ProjectEntity]:
        """模糊搜索项目"""
