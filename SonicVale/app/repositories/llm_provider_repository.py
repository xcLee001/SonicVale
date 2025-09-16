from typing import List, Optional, Sequence, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, Row, RowMapping
from app.models.po import LLMProviderPO


class LLMProviderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, llm_provider_id: int) -> Optional[LLMProviderPO]:
        """根据 ID 查询LLM供应商"""
        return self.db.get(LLMProviderPO, llm_provider_id)

    def get_all(self) -> Sequence[LLMProviderPO]:
        """获取所有LLM供应商"""
        return self.db.execute(select(LLMProviderPO)).scalars().all()

    def create(self, llm_provider_data: LLMProviderPO) -> LLMProviderPO:
        """新建LLM供应商"""
        self.db.add(llm_provider_data)
        self.db.commit()
        self.db.refresh(llm_provider_data)
        return llm_provider_data

    def update(self, llm_provider_id: int, llm_provider_data: dict) -> Optional[LLMProviderPO]:
        """更新LLM供应商"""
        llm_provider = self.get_by_id(llm_provider_id)
        if not llm_provider:
            return None
        for key, value in llm_provider_data.items():
            if value is not None:  # 只更新不为空的字段
                setattr(llm_provider, key, value)
        self.db.commit()
        self.db.refresh(llm_provider)
        return llm_provider

    def delete(self, llm_provider_id: int) -> bool:
        """删除LLM供应商"""
        llm_provider = self.get_by_id(llm_provider_id)
        if not llm_provider:
            return False
        self.db.delete(llm_provider)
        self.db.commit()
        return True

    def get_by_name(self, name: str) -> Optional[LLMProviderPO]:
        """根据名称查找LLM供应商"""
        stmt = select(LLMProviderPO).where(LLMProviderPO.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def search(self, keyword: str) -> Sequence[LLMProviderPO]:
        """模糊搜索"""
        stmt = select(LLMProviderPO).where(LLMProviderPO.name.ilike(f"%{keyword}%"))
        return self.db.execute(stmt).scalars().all()
