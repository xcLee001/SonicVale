import json
import logging

import requests
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

    def fetch_model_list(self, api_base_url: str, api_key: str | None):
        """Fetch models from an OpenAI-compatible /models endpoint."""
        if not api_base_url or not api_base_url.strip():
            return False, [], "Base URL 不能为空"

        base_url = api_base_url.strip().rstrip("/")
        if base_url.endswith("/chat/completions"):
            base_url = base_url[: -len("/chat/completions")]
        models_url = base_url if base_url.endswith("/models") else f"{base_url}/models"

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            resp = requests.get(models_url, headers=headers, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as e:
            return False, [], f"获取模型列表失败：{e}"
        except ValueError:
            return False, [], "获取模型列表失败：返回内容不是合法 JSON"

        items = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return False, [], "获取模型列表失败：返回格式中没有 data 列表"

        models = []
        seen = set()
        for item in items:
            if isinstance(item, str):
                model_id = item
            elif isinstance(item, dict):
                model_id = item.get("id") or item.get("name")
            else:
                model_id = None

            if model_id and model_id not in seen:
                models.append(model_id)
                seen.add(model_id)

        if not models:
            return False, [], "未获取到可用模型"
        return True, models, "获取成功"

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
        logging.info("测试结果为：%s", res)
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




