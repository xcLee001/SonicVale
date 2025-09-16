from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.po import ChapterPO


class ChapterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, chapter_id: int) -> Optional[ChapterPO]:
        """根据 ID 查询项目"""
        return self.db.get(ChapterPO, chapter_id)

    def get_all(self, project_id: int) -> Sequence[ChapterPO]:
        """获取指定项目下的所有章节"""
        stmt = select(ChapterPO).where(ChapterPO.project_id == project_id)
        return self.db.execute(stmt).scalars().all()

    def create(self, chapter_data: ChapterPO) -> ChapterPO:
        """新建项目"""
        self.db.add(chapter_data)
        self.db.commit()
        self.db.refresh(chapter_data)
        return chapter_data

    def update(self, chapter_id: int, chapter_data: dict) -> Optional[ChapterPO]:
        """更新项目"""
        chapter = self.get_by_id(chapter_id)
        if not chapter:
            return None
        for key, value in chapter_data.items():
            if value is not None:  # 只更新不为空的字段
                setattr(chapter, key, value)

        self.db.commit()
        self.db.refresh(chapter)
        return chapter

    def delete(self, chapter_id: int) -> bool:
        """删除章节"""
        project = self.get_by_id(chapter_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True
    # def delete_all_by_project_id(self, project_id: int) -> bool:
    #     """删除指定项目下的所有章节"""
    #     pos = self.get_all(project_id)
    #     for po in pos:
    #         self.db.delete(po)
    #     self.db.commit()
    #     return True

    def get_by_name(self, name: str, project_id: int) -> Optional[ChapterPO]:
        """根据项目ID和章节名称查找章节"""
        stmt = (
            select(ChapterPO)
            .where(ChapterPO.title == name)
            .where(ChapterPO.project_id == project_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def search(self, keyword: str) -> Sequence[ChapterPO]:
        """模糊搜索"""
        stmt = select(ChapterPO).where(ChapterPO.title.ilike(f"%{keyword}%"))
        return self.db.execute(stmt).scalars().all()