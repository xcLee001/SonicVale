import json
import os
import re
import shutil
import threading
from collections import defaultdict
from typing import List

from sqlalchemy import Sequence

from app.core.config import getConfigPath
from app.core.tts_engine import TTSEngine
from app.db.database import SessionLocal
from app.dto.line_dto import LineInitDTO
from app.entity.chapter_entity import ChapterEntity
from app.entity.line_entity import LineEntity
from app.models.po import ChapterPO, RolePO, LinePO

from app.repositories.chapter_repository import ChapterRepository
from app.repositories.line_repository import LineRepository

from app.core.prompts import get_context2lines_prompt
from app.repositories.llm_provider_repository import LLMProviderRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.role_repository import RoleRepository
from app.core.llm_engine import LLMEngine




class ChapterService:

    def __init__(self, repository: ChapterRepository):
        """注入 repository"""
        self.repository = repository

    def create_chapter(self,  entity: ChapterEntity):
        """创建新章节
        - 检查同名章节是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """

        chapter = self.repository.get_by_name(entity.title, entity.project_id)
        if chapter:
            return None
        # 手动将entity转化为po
        po = ChapterPO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = ChapterEntity(**data)

        # 将po转化为entity
        return entity


    def get_chapter(self, chapter_id: int) -> ChapterEntity | None:
        """根据 ID 查询章节"""
        po = self.repository.get_by_id(chapter_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = ChapterEntity(**data)
        return res

    def get_all_chapters(self,project_id: int) -> Sequence[ChapterEntity]:
        """获取所有章节列表"""
        pos = self.repository.get_all(project_id)
        # pos -> entities

        entities = [
            ChapterEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_chapter(self, chapter_id: int, data:dict) -> bool:
        """更新章节
        - 可以只更新部分字段
        - 检查同名冲突
        - 检查project_id不能改变
        """
        title = data["title"]
        project_id = data["project_id"]
        if self.repository.get_by_name(title, project_id) and self.repository.get_by_name(title,project_id).id != chapter_id:
            return False
        po = self.repository.get_by_id(chapter_id)
        # 防止改变project_id
        if po.project_id != project_id:
            return False
        self.repository.update(chapter_id, data)
        return True

    def delete_chapter(self, chapter_id: int) -> bool:
        """删除章节
        """
        db = SessionLocal()
        try :
            chapter = self.repository.get_by_id(chapter_id)
            res = self.repository.delete(chapter_id)
            # 删除章节下所有台词
            line_repository = LineRepository(db)
            line_res = line_repository.delete_all_by_chapter_id(chapter_id)
        #     移除资源内容
            # 删除该路径所有内容
            chapter_path = os.path.join(getConfigPath(), str(chapter.project_id), str(chapter_id))
            if os.path.exists(chapter_path):
                shutil.rmtree(chapter_path)  # 删除整个文件夹及其所有内容
                print(f"已删除目录及内容: {chapter_path}")
            else:
                print(f"目录不存在: {chapter_path}")
        finally:
            db.close()
        return res

    # 先获取章节内容
    def split_text(self, chapter_id: int, max_length: int = 800) -> List[str]:
        """
        将文本按标点断句，并按最大长度分组，确保每段以句号/问号/感叹号等结束。
        """
        content = self.get_chapter(chapter_id).text_content
        # 去掉空行
        content = "\n".join([line for line in content.split("\n") if line.strip()])

        # 使用正则分割成句子，保留句号/感叹号/问号
        sentences = re.findall(r'[^。！？]*[。！？]', content, re.MULTILINE | re.DOTALL)

        chunks = []
        buffer = ""

        for sentence in sentences:
            if len(buffer) + len(sentence) <= max_length:
                buffer += sentence
            else:
                if buffer:
                    chunks.append(buffer.strip())
                buffer = sentence

        if buffer:
            chunks.append(buffer.strip())

        return chunks  # ✅ 别忘了这个！

    # 然后进行划分

    # 然后循环解析，并保存

    def para_content(self, chapter_id: int,content: str = None,role_names: List[str] = None,emotion_names: List[str] = None,strength_names: List[str] = None):
        db = SessionLocal()
        try :
    #         获取content
            chapter = self.repository.get_by_id(chapter_id)
            # content = chapter.text_content
    #          获取角色列表
    #         role_repository = RoleRepository(db)
    #         roles = role_repository.get_all(chapter.project_id)
    #         role_names = [role.name for role in roles]
    #         组装prompt
            prompt = get_context2lines_prompt(role_names, content,emotion_names,strength_names)

        #   获取llm_provider

            project_repository = ProjectRepository(db)
            project = project_repository.get_by_id(chapter.project_id)
            llm_provider_id = project.llm_provider_id
            #
            llm_provider_repository = LLMProviderRepository(db)
            llm_provider = llm_provider_repository.get_by_id(llm_provider_id)
            llm = LLMEngine(llm_provider.api_key, llm_provider.api_base_url, project.llm_model)
            print("开始内容解析")
            try:
                result = llm.generate_text(prompt)
                # 解析json，并且构造为List[LineInitDTO]
                # 解析 JSON 字符串为 Python 对象
                parsed_data = llm.save_load_json(result)
                # parsed_data = json.loads(result)
                # 构造 List[LineInitDTO]
                line_dtos: List[LineInitDTO] = [LineInitDTO(**item) for item in parsed_data]
                return  line_dtos
            except Exception as e:
                print("调用 LLM 出错：", e)
                return None
        finally:
            db.close()


    # 导出指令
    def get_prompt_content(self, chapter_id):
        db = SessionLocal()
        try:
            #         获取content
            chapter = self.repository.get_by_id(chapter_id)
            content = chapter.text_content
            #          获取角色列表
            role_repository = RoleRepository(db)
            roles = role_repository.get_all(chapter.project_id)
            role_names = [role.name for role in roles]
            #         组装prompt
            prompt = get_context2lines_prompt(role_names, content)
            return  prompt
        finally:
            db.close()




