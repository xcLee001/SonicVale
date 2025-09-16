from sqlalchemy import Sequence

from app.entity.multi_emotion_voice_entity import MultiEmotionVoiceEntity
from app.models.po import MultiEmotionVoicePO
from app.repositories.multi_emotion_voice_repository import MultiEmotionVoiceRepository


class MultiEmotionVoiceService:

    def __init__(self, repository: MultiEmotionVoiceRepository):
        """注入 repository"""
        self.repository = repository

    def create_multi_emotion_voice(self,  entity: MultiEmotionVoiceEntity):
        """创建新多情绪音色变体
        - 检查同名多情绪音色变体是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """
        if entity.voice_id is None or entity.emotion_id is None or entity.strength_id is None:
            return None
        multi_emotion_voice = self.repository.get_by_voice_id_emotion_id_strength_id(entity.voice_id, entity.emotion_id, entity.strength_id)
        if multi_emotion_voice:
            return None
        po = MultiEmotionVoicePO(**entity.__dict__)
        res = self.repository.create(po)
        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = MultiEmotionVoiceEntity(**data)

        # 将po转化为entity
        return entity
    # 根据voice_id,emotion_id,strength_id查询多情绪音色变体
    def get_multi_emotion_voice_by_voice_id_emotion_id_strength_id(self, voice_id: int, emotion_id: int, strength_id: int) -> MultiEmotionVoiceEntity | None:
        """根据voice_id,emotion_id,strength_id查询多情绪音色变体"""
        po = self.repository.get_by_voice_id_emotion_id_strength_id(voice_id, emotion_id, strength_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = MultiEmotionVoiceEntity(**data)
        return res

    def get_multi_emotion_voice_by_voice_id(self, voice_id: int) -> list[MultiEmotionVoiceEntity] | None:
        """根据 voice_id 查询所有的多情绪音色变体"""
        pos = self.repository.get_by_voice_id(voice_id)
        entities = [
            MultiEmotionVoiceEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def get_multi_emotion_voice_by_id(self, multi_emotion_voice_id: int) -> MultiEmotionVoiceEntity | None:
        """根据 ID 获取多情绪音色变体"""
        po = self.repository.get_by_id(multi_emotion_voice_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = MultiEmotionVoiceEntity(**data)
        return res
    def get_all_multi_emotion_voices(self) -> list[MultiEmotionVoiceEntity]:
        """获取所有多情绪音色变体列表"""
        pos = self.repository.get_all()
        # pos -> entities

        entities = [
            MultiEmotionVoiceEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_multi_emotion_voice(self, multi_emotion_voice_id: int, data:dict) -> bool:
        """更新多情绪音色变体
        - 可以只更新部分字段
        - 检查同名冲突
        - 检查project_id不能改变
        """
        self.repository.update(multi_emotion_voice_id, data)
        return True

    def delete_multi_emotion_voice(self, multi_emotion_voice_id: int) -> bool:
        """删除多情绪音色变体
        """
        res = self.repository.delete(multi_emotion_voice_id)
        return res

#     删除voice下所有多情绪音色变体
    def delete_multi_emotion_voice_by_voice_id(self, voice_id: int) -> bool:
        """删除voice下所有多情绪音色变体
        """
        res = self.repository.delete_multi_emotion_voice_by_voice_id(voice_id)
        return res
