from typing import Optional, Sequence, Any

from sqlalchemy.orm import Session, Query

from app.models.po import MultiEmotionVoicePO


class MultiEmotionVoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[MultiEmotionVoicePO]:
        """通过id获取多情绪音色"""
        return self.db.query(MultiEmotionVoicePO).filter(MultiEmotionVoicePO.id == id).first()

    # 根据voice_id,emotion_id,strength_id获取多情绪音色
    def get_by_voice_id_emotion_id_strength_id(self, voice_id: int, emotion_id: int, strength_id: int) -> type[MultiEmotionVoicePO] | None:
        """根据voice_id,emotion_id,strength_id获取多情绪音色"""
        return self.db.query(MultiEmotionVoicePO).filter(MultiEmotionVoicePO.voice_id == voice_id,
                                                         MultiEmotionVoicePO.emotion_id == emotion_id,
                                                         MultiEmotionVoicePO.strength_id == strength_id).one_or_none()
    # 根据voice_id获取多情绪音色
    def get_by_voice_id(self, voice_id: int) -> Sequence[type[MultiEmotionVoicePO]]:
        """根据voice_id获取多情绪音色"""
        return self.db.query(MultiEmotionVoicePO).filter(MultiEmotionVoicePO.voice_id == voice_id).all()

    def get_all(self) -> list[type[MultiEmotionVoicePO]]:
        """获取所有多情绪音色"""
        return self.db.query(MultiEmotionVoicePO).all()

    def create(self, multi_emotion_voice: MultiEmotionVoicePO) -> MultiEmotionVoicePO:
        """创建多情绪音色"""

        self.db.add(multi_emotion_voice)
        self.db.commit()
        self.db.refresh(multi_emotion_voice)
        return multi_emotion_voice

    def update(self, id: int, data: dict) -> Optional[MultiEmotionVoicePO]:
        """更新多情绪音色"""
        multi_emotion_voice = self.get_by_id(id)
        if not multi_emotion_voice:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(multi_emotion_voice, key, value)
        self.db.commit()
        self.db.refresh(multi_emotion_voice)
        return multi_emotion_voice

    def delete(self, id: int) -> bool:
        """删除多情绪音色"""
        multi_emotion_voice = self.get_by_id(id)
        if not multi_emotion_voice:
            return False
        self.db.delete(multi_emotion_voice)
        self.db.commit()
        return True

    def delete_multi_emotion_voice_by_voice_id(self, voice_id):
        """通过音色id删除所有的多音色"""
        multi_voices = self.get_by_voice_id(voice_id)
        for multi_voice in multi_voices:
            self.db.delete(multi_voice)
        self.db.commit()
        return True


