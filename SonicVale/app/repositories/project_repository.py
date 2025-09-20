from typing import List, Optional, Sequence, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, Row, RowMapping
from app.models.po import ProjectPO


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, project_id: int) -> Optional[ProjectPO]:
        """根据 ID 查询项目"""
        return self.db.get(ProjectPO, project_id)

    def get_all(self) -> Sequence[ProjectPO]:
        """获取所有项目"""
        return self.db.execute(select(ProjectPO)).scalars().all()

    def create(self, project_data: ProjectPO) -> ProjectPO:
        """新建项目"""
        self.db.add(project_data)
        self.db.commit()
        self.db.refresh(project_data)
        return project_data

    def update(self, project_id: int, project_data: dict) -> Optional[ProjectPO]:
        """更新项目"""
        project = self.get_by_id(project_id)
        if not project:
            return None
        for key, value in project_data.items():
            setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: int) -> bool:
        """删除项目"""
        project = self.get_by_id(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True

    def get_by_name(self, name: str) -> Optional[ProjectPO]:
        """根据名称查找项目"""
        stmt = select(ProjectPO).where(ProjectPO.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def search(self, keyword: str) -> Sequence[ProjectPO]:
        """模糊搜索"""
        stmt = select(ProjectPO).where(ProjectPO.name.ilike(f"%{keyword}%"))
        return self.db.execute(stmt).scalars().all()
