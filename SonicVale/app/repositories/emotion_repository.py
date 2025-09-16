from typing import Optional, Sequence

from sqlalchemy.orm import Session

from app.models.po import EmotionPO


class EmotionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[EmotionPO]:
        """通过id获取情绪"""
        return self.db.query(EmotionPO).filter(EmotionPO.id == id).first()

    def get_by_name(self, name: str) -> Optional[EmotionPO]:
        """通过名称获取情绪"""
        return self.db.query(EmotionPO).filter(EmotionPO.name == name).first()

    def get_all(self) -> list[type[EmotionPO]]:
        """获取所有情绪"""
        return self.db.query(EmotionPO).all()

    def create(self, emotion: EmotionPO) -> EmotionPO:
        """创建情绪"""

        self.db.add(emotion)
        self.db.commit()
        self.db.refresh(emotion)
        return emotion

    def update(self, id: int, data: dict) -> Optional[EmotionPO]:
        """更新情绪"""
        emotion = self.get_by_id(id)
        if not emotion:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(emotion, key, value)
        self.db.commit()
        self.db.refresh(emotion)
        return emotion

    def delete(self, id: int) -> bool:
        """删除情绪"""
        emotion = self.get_by_id(id)
        if not emotion:
            return False
        self.db.delete(emotion)
        self.db.commit()
        return True


