import json

from aiohttp.abc import HTTPException
from sqlalchemy import Sequence

from app.core.llm_engine import LLMEngine
from app.entity.llm_provider_entity import LLMProviderEntity
from app.models.po import LLMProviderPO

from app.repositories.llm_provider_repository import LLMProviderRepository


class LLMProviderService:

    def __init__(self, repository: LLMProviderRepository):
        """注入 repository"""
        self.repository = repository

    def create_llm_provider(self,  entity: LLMProviderEntity):
        """创建新LLM供应商
        - 检查同名LLM供应商是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """
        llm_provider = self.repository.get_by_name(entity.name)
        if llm_provider:
            return None
        # 手动将entity转化为po
        po = LLMProviderPO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = LLMProviderEntity(**data)

        # 将po转化为entity
        return entity


    def get_llm_provider(self, llm_provider_id: int) -> LLMProviderEntity | None:
        """根据 ID 查询LLM供应商"""
        po = self.repository.get_by_id(llm_provider_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = LLMProviderEntity(**data)
        return res

    def get_all_llm_providers(self) -> Sequence[LLMProviderEntity]:
        """获取所有LLM供应商列表"""
        pos = self.repository.get_all()
        # pos -> entities

        entities = [
            LLMProviderEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_llm_provider(self, llm_provider_id: int, data:dict) -> bool:
        """更新LLM供应商
        - 可以只更新部分字段
        - 检查同名冲突
        """
        name = data["name"]
        if self.repository.get_by_name(name) and self.repository.get_by_name(name).id != llm_provider_id:
            return False
        self.repository.update(llm_provider_id, data)
        return True

    def delete_llm_provider(self, llm_provider_id: int) -> bool:
        """删除LLM供应商
        - 可以添加业务校验，例如LLM供应商下有章节是否允许删除
        - 后续需要级联删除所有章节内容
        """
        res = self.repository.delete(llm_provider_id)
        return res

    def test_llm_provider(self, entity: LLMProviderEntity):
        """测试LLM供应商"""
        # 按逗号划分模型名称
        if entity.api_base_url is None or entity.api_key is None or entity.model_list is None:
            return False
        model_lists = entity.model_list.split(",")
        custom_params = entity.custom_params
        llm = LLMEngine(entity.api_key, entity.api_base_url, model_lists[0],custom_params)
        try:
            res = llm.generate_text_test("请输出一份用户信息，严格使用 JSON 格式，不要包含任何额外文字。字段包括：name, age, city")
        except Exception as e:
            return  False,str(e)
        print('测试结果为：', res)
        if res is None:
            return False,"LLM 未返回任何内容"

        # 7. 校验返回是否为合法 JSON
        try:
            # res = res.replace("```json",'')
            # res = res.replace("```",'')
            json.loads(res)
        except json.JSONDecodeError:
            return False, "LLM 返回的内容不是合法 JSON，请检查模型 / 提示词"
        return True,"测试成功"




