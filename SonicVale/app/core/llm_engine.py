# app/core/llm_engine.py
import json
# app/core/llm_engine.py

import re
import time
import random
import openai

from app.core.prompts import get_auto_fix_json_prompt


class LLMEngine:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        """
        api_key: LLM API Key
        base_url: OpenAI-compatible API URL（例如企业版/自建 LLM）
        model_name: 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")  # 去掉末尾斜杠
        self.model_name = model_name
        openai.api_key = api_key
        openai.api_base = self.base_url

    def _extract_result_tag(self, text: str) -> str:
        """提取 <result> 标签内容"""
        match = re.search(r"<result>(.*?)</result>", text, re.DOTALL)
        if not match:
            raise ValueError("Response does not contain <result>...</result> tag")
        return match.group(1).strip()

    def generate_text_test(self, prompt: str) -> str:
        """
        测试：生成结果并返回
        """
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            timeout=3000,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    def generate_text(self, prompt: str, retries: int = 3, delay: float = 1.0) -> str:
        """
        流式生成：边生成边输出
        """
        for attempt in range(retries):
            try:
                # 开启流式
                response = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    timeout=3000,
                    response_format={"type": "json_object"}
                )

                # 拼接 delta.content
                full_text = ""
                for chunk in response:
                    if 'choices' in chunk and 'delta' in chunk['choices'][0]:
                        content = chunk['choices'][0]['delta'].get('content')
                        if content:
                            print(content, end="", flush=True)  # 实时输出
                            full_text += content

                print("\n--- 输出完成 ---")
                return full_text

            except Exception as e:
                if attempt < retries - 1:
                    sleep_time = delay * (2 ** attempt) + random.random()
                    time.sleep(sleep_time)
                else:
                    raise e
    # json输出问题解决
    def save_load_json(self, json_str: str):
        #先加载json
        try:
            json_obj = json.loads(json_str)
            return json_obj
        except json.JSONDecodeError:
            print("JSON 解析错误，尝试修复")
            prompt = get_auto_fix_json_prompt(json_str)
            res = self.generate_text(prompt)
            return json.loads(res)



def main():
    # 测试配置（可以用你自己的 API）
    api_key = "sk-89c8b48798b6422fa8e9b59664dabf1e"
    api_url = "https://api.deepseek.com"
    model_name = "deepseek-reasoner"

    llm = LLMEngine(api_key, api_url, model_name)

    # 测试 prompt
    prompt = "输出<result>标签的结果，例如：<result>这是测试内容</result>。问题：你好，请问你是谁"

    try:
        result = llm.generate_text(prompt)
        print("LLM 返回结果（提取 <result> 标签内容）：")
        print(result)
    except Exception as e:
        print("调用 LLM 出错：", e)


if __name__ == "__main__":
    main()