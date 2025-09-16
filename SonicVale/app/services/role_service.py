from sqlalchemy import Sequence

from app.entity.role_entity import RoleEntity
from app.models.po import RolePO
from app.repositories.role_repository import RoleRepository


class RoleService:

    def __init__(self, repository: RoleRepository):
        """注入 repository"""
        self.repository = repository

    def create_role(self,  entity: RoleEntity):
        """创建新角色
        - 检查同名角色是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """

        role = self.repository.get_by_name(entity.name, entity.project_id)
        if role:
            return None
        # 手动将entity转化为po
        po = RolePO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = RoleEntity(**data)

        # 将po转化为entity
        return entity


    def get_role(self, role_id: int) -> RoleEntity | None:
        """根据 ID 查询角色"""
        po = self.repository.get_by_id(role_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = RoleEntity(**data)
        return res

    def get_all_roles(self,project_id: int) -> Sequence[RoleEntity]:
        """获取所有角色列表"""
        pos = self.repository.get_all(project_id)
        # pos -> entities

        entities = [
            RoleEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_role(self, role_id: int, data:dict) -> bool:
        """更新角色
        - 可以只更新部分字段
        - 检查同名冲突
        - 检查project_id不能改变
        """
        name = data["name"]
        project_id = data["project_id"]
        if self.repository.get_by_name(name, project_id) and self.repository.get_by_name(name,project_id).id != role_id:
            return False
        po = self.repository.get_by_id(role_id)
        # 防止改变project_id
        if po.project_id != project_id:
            return False
        self.repository.update(role_id, data)
        return True

    def delete_role(self, role_id: int) -> bool:
        """删除角色
        """
        res = self.repository.delete(role_id)
        return res
