import logging

import requests

from app.entity.tts_provider_entity import TTSProviderEntity
from app.models.po import TTSProviderPO
from app.repositories.tts_provider_repository import TTSProviderRepository


class TTSProviderService:

    SUPPORTED_ENGINE_TYPES = {"index_tts_2_0", "index_tts_2_5"}
    BUILTIN_PROVIDERS = (
        {
            "id": 1,
            "name": "IndexTTS 2.0",
            "engine_type": "index_tts_2_0",
        },
        {
            "id": 2,
            "name": "IndexTTS 2.5",
            "engine_type": "index_tts_2_5",
        },
    )

    def __init__(self, repository: TTSProviderRepository):
        """注入 repository"""
        self.repository = repository

    def get_all_tts_providers(self) -> list[TTSProviderEntity]:
        """查询所有tts供应商"""
        pos = self.repository.get_all()
        res = [TTSProviderEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")}) for po in pos]
        return res

    def get_tts_provider(self, tts_provider_id: int) -> TTSProviderEntity | None:
        """根据 ID 查询tts供应商"""
        po = self.repository.get_by_id(tts_provider_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = TTSProviderEntity(**data)
        return res

    def update_tts_provider(self, tts_provider_id: int, data:dict) -> bool:
        """内置 TTS 引擎只允许更新服务 URL。"""
        provider = self.repository.get_by_id(tts_provider_id)
        if provider is None or provider.engine_type not in self.SUPPORTED_ENGINE_TYPES:
            return False
        api_base_url = str(data.get("api_base_url") or "").strip().rstrip("/")
        if not api_base_url:
            return False
        self.repository.update(tts_provider_id, {"api_base_url": api_base_url})
        return True

    def delete_tts_provider(self, tts_provider_id: int) -> bool:
        """删除tts供应商
        """
        res = self.repository.delete(tts_provider_id)
        return res

    def ensure_builtin_tts_providers(self):
        """初始化并锁定 IndexTTS 2.0 / 2.5 两个内置引擎。"""
        for config in self.BUILTIN_PROVIDERS:
            provider = self.repository.get_by_id(config["id"])
            if provider is None:
                self.repository.create(TTSProviderPO(
                    id=config["id"],
                    name=config["name"],
                    status=1,
                    api_base_url="",
                    api_key="",
                    engine_type=config["engine_type"],
                ))
                continue

            self.repository.update(provider.id, {
                "name": config["name"],
                "engine_type": config["engine_type"],
                "status": 1,
            })

    def test_tts_provider(self, entity: TTSProviderEntity):
        # 拿到url
        api_base_url = entity.api_base_url
        if not api_base_url:
            return False
        # ping api
        # 调用
        try:
            resp = requests.get(api_base_url.rstrip("/"), timeout=5)

            # 如果返回 200-399 都认为是通的（有些服务会 302 重定向）
            if 200 <= resp.status_code < 400:
                try:
                    data = resp.json()
                    if "endpoints" not in data:
                        logging.error("TTS provider test failed: 'endpoints' missing in response")
                        return False

                    if entity.engine_type == "index_tts_2_5":
                        model_resp = requests.get(
                            f"{api_base_url.rstrip('/')}/v1/models",
                            timeout=5,
                        )
                        model_resp.raise_for_status()
                        model_data = model_resp.json()
                        return model_data.get("name") == "IndexTTS-2.5"
                    else:
                        return True
                except ValueError:
                    logging.error("TTS provider test failed: response is not valid JSON")
                    return False
            else:
                logging.error("TTS provider test failed: status %s", resp.status_code)
                return False

        except Exception as e:
            logging.exception("TTS provider test failed: %s", e)
            return False



