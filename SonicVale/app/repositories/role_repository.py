from typing import Optional

from sqlalchemy import Sequence, select
from sqlalchemy.orm import Session

from app.models.po import RolePO


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[RolePO]:
        """根据 ID 查询角色"""
        return self.db.get(RolePO, id)

    def get_all(self,project_id: int) -> Sequence[RolePO]:
        """获取项目下所有角色"""
        return self.db.execute(select(RolePO).where(RolePO.project_id == project_id)).scalars().all()


    def create(self, data: RolePO) -> RolePO:
        """新增角色"""
        self.db.add(data)
        self.db.commit()
        self.db.refresh(data)
        return data


    def update(self, role_id: int, role_data: dict) -> Optional[RolePO]:
        """更新角色信息"""
        role = self.get_by_id(role_id)
        if not role:
            return None
        for key, value in role_data.items():
            if value is not None:  # 只更新不为空的字段
                setattr(role, key, value)

        self.db.commit()
        self.db.refresh(role)
        return role

    def delete(self, role_id: int) -> bool:
        """删除项目"""
        role = self.get_by_id(role_id)
        if not role:
            return False
        self.db.delete(role)
        self.db.commit()
        return True


    def get_by_name(self, name: str,project_id: int) -> Optional[RolePO]:
        """根据名称查找项目下的角色信息"""
        return self.db.execute(select(RolePO).where(RolePO.name == name,RolePO.project_id == project_id)).scalars().first()


