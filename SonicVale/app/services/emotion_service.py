from sqlalchemy import Sequence

from app.entity.emotion_entity import EmotionEntity
from app.models.po import EmotionPO
from app.repositories.emotion_repository import EmotionRepository


class EmotionService:

    def __init__(self, repository: EmotionRepository):
        """注入 repository"""
        self.repository = repository

    def create_emotion(self,  entity: EmotionEntity):
        """创建新情绪枚举
        - 检查同名情绪枚举是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """

        emotion = self.repository.get_by_name(entity.name)
        if emotion:
            return None
        # 手动将entity转化为po
        po = EmotionPO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = EmotionEntity(**data)

        # 将po转化为entity
        return entity


    def get_emotion(self, emotion_id: int) -> EmotionEntity | None:
        """根据 ID 查询情绪枚举"""
        po = self.repository.get_by_id(emotion_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = EmotionEntity(**data)
        return res

    def get_all_emotions(self) -> Sequence[EmotionEntity]:
        """获取所有情绪枚举列表"""
        pos = self.repository.get_all()
        # pos -> entities

        entities = [
            EmotionEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_emotion(self, emotion_id: int, data:dict) -> bool:
        """更新情绪枚举
        - 可以只更新部分字段
        """
        name = data.get("name")
        if self.repository.get_by_name(name):
            return False
        self.repository.update(emotion_id, data)
        return True

    def delete_emotion(self, emotion_id: int) -> bool:
        """删除情绪枚举
        """
        res = self.repository.delete(emotion_id)
        return res

    def get_emotion_by_name(self, name: str) -> EmotionEntity | None:
        """根据名称查询情绪枚举"""
        po = self.repository.get_by_name(name)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = EmotionEntity(**data)
        return res
