from sqlalchemy import Sequence

from app.entity.voice_entity import VoiceEntity
from app.models.po import VoicePO
from app.repositories.multi_emotion_voice_repository import MultiEmotionVoiceRepository
from app.repositories.voice_repository import VoiceRepository


class VoiceService:

    def __init__(self, repository: VoiceRepository,multi_emotion_voice_repository: MultiEmotionVoiceRepository):
        """注入 repository"""
        self.repository = repository
        self.multi_emotion_voice_repository = multi_emotion_voice_repository

    def create_voice(self,  entity: VoiceEntity):
        """创建新音色
        - 检查同名音色是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """

        voice = self.repository.get_by_name(entity.name, entity.tts_provider_id)
        if voice:
            return None
        # 手动将entity转化为po
        po = VoicePO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = VoiceEntity(**data)

        # 将po转化为entity
        return entity


    def get_voice(self, voice_id: int) -> VoiceEntity | None:
        """根据 ID 查询音色"""
        po = self.repository.get_by_id(voice_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = VoiceEntity(**data)
        return res

    def get_all_voices(self,tts_provider_id: int) -> Sequence[VoiceEntity]:
        """获取所有音色列表"""
        pos = self.repository.get_all(tts_provider_id)
        # pos -> entities

        entities = [
            VoiceEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_voice(self, voice_id: int, data:dict) -> bool:
        """更新音色
        - 可以只更新部分字段
        - 检查同名冲突
        - 检查project_id不能改变
        """
        name = data["name"]
        tts_provider_id = data["tts_provider_id"]
        if self.repository.get_by_name(name, tts_provider_id) and self.repository.get_by_name(name,tts_provider_id).id != voice_id:
            return False
        po = self.repository.get_by_id(voice_id)
        # 防止改变project_id
        if po.tts_provider_id != tts_provider_id:
            return False
        self.repository.update(voice_id, data)
        return True

    def delete_voice(self, voice_id: int) -> bool:
        """删除音色,需要保证事务
        """

        res = self.repository.delete(voice_id)
        self.multi_emotion_voice_repository.delete_multi_emotion_voice_by_voice_id(voice_id)
        return res
