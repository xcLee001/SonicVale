from typing import Optional

from sqlalchemy import Sequence, select
from sqlalchemy.orm import Session

from app.models.po import TTSProviderPO


class TTSProviderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[TTSProviderPO]:
        """根据 ID 查询tts供应商"""
        return self.db.get(TTSProviderPO, id)

    def get_all(self) -> Sequence[TTSProviderPO]:
        """获取tts下所有tts供应商"""
        return self.db.execute(select(TTSProviderPO)).scalars().all()


    def create(self, data: TTSProviderPO) -> TTSProviderPO:

        """新增tts供应商"""
        self.db.add(data)
        self.db.commit()
        self.db.refresh(data)
        return data


    def update(self, tts_provider_id: int, voice_data: dict) -> Optional[TTSProviderPO]:
        """更新tts供应商信息"""
        voice = self.get_by_id(tts_provider_id)
        if not voice:
            return None
        for key, value in voice_data.items():
            if value is not None:  # 只更新不为空的字段
                setattr(voice, key, value)

        self.db.commit()
        self.db.refresh(voice)
        return voice

    # def delete(self, voice_id: int) -> bool:
    #     """删除项目"""
    #     voice = self.get_by_id(voice_id)
    #     if not voice:
    #         return False
    #     self.db.delete(voice)
    #     self.db.commit()
    #     return True
    #
    #
    def get_by_name(self, name: str) -> Optional[TTSProviderPO]:
        """根据名称查找项目下的tts供应商信息"""
        return self.db.execute(select(TTSProviderPO).where(TTSProviderPO.name == name)).scalars().first()


