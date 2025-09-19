from typing import List, Optional, Sequence, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, Row, RowMapping
from app.models.po import PromptPO


class PromptRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, prompt_id: int) -> Optional[PromptPO]:
        """根据 ID 查询提示词"""
        return self.db.get(PromptPO, prompt_id)

    def get_all(self) -> Sequence[PromptPO]:
        """获取所有提示词"""
        return self.db.execute(select(PromptPO)).scalars().all()

    def create(self, prompt_data: PromptPO) -> PromptPO:
        """新建提示词"""
        self.db.add(prompt_data)
        self.db.commit()
        self.db.refresh(prompt_data)
        return prompt_data

    def update(self, prompt_id: int, prompt_data: dict) -> Optional[PromptPO]:
        """更新提示词"""
        prompt = self.get_by_id(prompt_id)
        if not prompt:
            return None
        for key, value in prompt_data.items():
            if value is not None:  # 只更新不为空的字段
                setattr(prompt, key, value)
        self.db.commit()
        self.db.refresh(prompt)
        return prompt

    def delete(self, prompt_id: int) -> bool:
        """删除提示词"""
        prompt = self.get_by_id(prompt_id)
        if not prompt:
            return False
        self.db.delete(prompt)
        self.db.commit()
        return True

    def get_by_name(self, name: str) -> Optional[PromptPO]:
        """根据名称查找提示词"""
        stmt = select(PromptPO).where(PromptPO.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    # 根据任务查询，返回多个提示词
    def get_by_task(self, task: str) -> Sequence[PromptPO]:
        stmt = select(PromptPO).where(PromptPO.task == task)
        return self.db.execute(stmt).scalars().all()


    def search(self, keyword: str) -> Sequence[PromptPO]:
        """模糊搜索"""
        stmt = select(PromptPO).where(PromptPO.name.ilike(f"%{keyword}%"))
        return self.db.execute(stmt).scalars().all()
