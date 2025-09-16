from typing import Optional, Sequence

from sqlalchemy.orm import Session

from app.models.po import StrengthPO


class StrengthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[StrengthPO]:
        """通过id获取情绪强弱"""
        return self.db.query(StrengthPO).filter(StrengthPO.id == id).first()

    def get_by_name(self, name: str) -> Optional[StrengthPO]:
        """通过名称获取情绪强弱"""
        return self.db.query(StrengthPO).filter(StrengthPO.name == name).first()

    def get_all(self) -> list[type[StrengthPO]]:
        """获取所有情绪强弱"""
        return self.db.query(StrengthPO).all()

    def create(self, strength: StrengthPO) -> StrengthPO:
        """创建情绪强弱"""
        self.db.add(strength)
        self.db.commit()
        self.db.refresh(strength)
        return strength

    def update(self, id: int, data: dict) -> Optional[StrengthPO]:
        """更新情绪强弱"""
        strength = self.get_by_id(id)
        if not strength:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(strength, key, value)
        self.db.commit()
        self.db.refresh(strength)
        return strength

    def delete(self, id: int) -> bool:
        """删除情绪强弱"""
        strength = self.get_by_id(id)
        if not strength:
            return False
        self.db.delete(strength)
        self.db.commit()
        return True


