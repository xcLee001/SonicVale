# 初始化 router
import asyncio
import io
import json
import logging
import os
import traceback

from typing import List


from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Form


from app.core.response import Res
from app.core.text_correct_engine import TextCorrectorFinal
from app.core.ws_manager import manager
from app.db.database import get_db, SessionLocal
from app.dto.chapter_dto import ChapterResponseDTO, ChapterCreateDTO
from app.dto.line_dto import LineInitDTO, LineCreateDTO, LineResponseDTO
from app.entity.chapter_entity import ChapterEntity
from app.repositories.chapter_repository import ChapterRepository
from app.repositories.emotion_repository import EmotionRepository
from app.repositories.line_repository import LineRepository
from app.repositories.llm_provider_repository import LLMProviderRepository
from app.repositories.multi_emotion_voice_repository import MultiEmotionVoiceRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.prompt_repository import PromptRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.strength_repository import StrengthRepository
from app.repositories.tts_provider_repository import TTSProviderRepository
from app.repositories.voice_repository import VoiceRepository

from app.services.chapter_service import ChapterService
from app.services.emotion_service import EmotionService
from app.services.line_service import LineService
from app.services.multi_emotion_voice_service import MultiEmotionVoiceService
from app.services.project_service import ProjectService
from app.services.prompt_service import PromptService
from app.services.role_service import RoleService
from app.services.strength_service import StrengthService
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/chapters", tags=["Chapters"])


# 依赖注入（实际项目可用 DI 容器）

def get_chapter_service(db: Session = Depends(get_db)) -> ChapterService:
    repository = ChapterRepository(db)  # ✅ 传入 db
    return ChapterService(repository)

def get_line_service(db: Session = Depends(get_db)) -> LineService:
    repository = LineRepository(db)
    role_repository = RoleRepository(db)
    tts_provider_repository = TTSProviderRepository(db)
    return LineService(repository,role_repository,tts_provider_repository)

def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    repository = ProjectRepository(db)
    return ProjectService(repository)

def get_voice_service(db: Session = Depends(get_db)) -> VoiceService:
    repository = VoiceRepository(db)
    multi_emotion_voice_repository = MultiEmotionVoiceRepository(db)
    return VoiceService(repository,multi_emotion_voice_repository)

def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    repository = RoleRepository(db)
    return RoleService(repository)

def get_emotion_service(db: Session = Depends(get_db)) -> EmotionService:
    repository = EmotionRepository(db)
    return EmotionService(repository)

def get_strength_service(db: Session = Depends(get_db)) -> StrengthService:
    repository = StrengthRepository(db)
    return StrengthService(repository)

def get_multi_emotion_voice_service(db: Session = Depends(get_db)) -> MultiEmotionVoiceService:
    repository = MultiEmotionVoiceRepository(db)
    return MultiEmotionVoiceService(repository)

def get_prompt_service(db: Session = Depends(get_db)) -> PromptService:
    repository = PromptRepository(db)
    return PromptService(repository)

@router.post("", response_model=Res[ChapterResponseDTO],
             summary="创建章节",
             description="根据项目ID创建章节，章节名称在同一项目下不可重复" )
async def create_chapter(dto: ChapterCreateDTO, chapter_service: ChapterService = Depends(get_chapter_service),
                   project_service: ProjectService = Depends(get_project_service)):
    """创建章节"""
    try:
        # DTO → Entity
        entity = ChapterEntity(**dto.__dict__)
        # 判断project_id是否存在
        project = project_service.get_project(dto.project_id)
        if project is None:
            return Res(data=None, code=400, message=f"项目 '{dto.project_id}' 不存在")
        # 调用 Service 创建项目（返回 True/False）
        entityRes = chapter_service.create_chapter(entity)

        # 返回统一 Response
        if entityRes is not None:
            # 创建成功，可以返回 DTO 或者部分字段
            res = ChapterResponseDTO(**entityRes.__dict__)
            return Res(data=res, code=200, message="创建成功")
        else:
            return Res(data=None, code=400, message=f"章节 '{entity.title}' 已存在")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{chapter_id}", response_model=Res[ChapterResponseDTO],
            summary="查询章节",
            description="根据章节id查询章节信息")
async def get_chapter(chapter_id: int, chapter_service: ChapterService = Depends(get_chapter_service)):
    entity = chapter_service.get_chapter(chapter_id)
    if entity:
        res = ChapterResponseDTO(**entity.__dict__)
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=None, code=404, message="项目不存在")

@router.get("/project/{project_id}", response_model=Res[List[ChapterResponseDTO]],
            summary="查询项目下的所有章节",
            description="根据项目id查询项目下的所有章节信息")
async def get_all_chapters(project_id: int, chapter_service: ChapterService = Depends(get_chapter_service)):
    entities = chapter_service.get_all_chapters(project_id)
    if entities:
        res = [ChapterResponseDTO(**e.__dict__) for e in entities]
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=[], code=404, message="项目不存在章节")

# 修改，传入的参数是id
@router.put("/{chapter_id}", response_model=Res[ChapterCreateDTO],
            summary="修改章节",
            description="根据章节id修改章节信息,并且不能修改项目id")
async def update_chapter(chapter_id: int, dto: ChapterCreateDTO, chapter_service: ChapterService = Depends(get_chapter_service)):
    chapter = chapter_service.get_chapter(chapter_id)
    if chapter is None:
        return Res(data=None, code=404, message="章节不存在")
    res = chapter_service.update_chapter(chapter_id, dto.dict(exclude_unset=True))
    if res:
        return Res(data=dto, code=200, message="修改成功")
    else:
        return Res(data=None, code=400, message="修改失败")


# 根据id，删除
@router.delete("/{chapter_id}", response_model=Res,
               summary="删除章节",
               description="根据章节id删除章节信息,并且级联删除")
async def delete_chapter(chapter_id: int, chapter_service: ChapterService = Depends(get_chapter_service)):
    success = chapter_service.delete_chapter(chapter_id)

    if success:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败或章节不存在")


# 根据内容进行解析得到json,初次解析，然后可编辑角色昵称以及内容，以及可以合并上下或者增加。（json都是多条，角色+台词）
@router.get(
    "/get-lines/{project_id}/{chapter_id}",
    response_model=Res[str],
    summary="根据内容进行解析得到json",
    description="根据内容进行解析得到json"
)
async def get_lines(
    project_id: int,
    chapter_id: int,
    chapter_service: ChapterService = Depends(get_chapter_service),
    line_service: LineService = Depends(get_line_service),
    role_service: RoleService = Depends(get_role_service),
    emotion_service: EmotionService = Depends(get_emotion_service),
    strength_service: StrengthService = Depends(get_strength_service),
    prompt_service: PromptService = Depends(get_prompt_service),
    project_service: ProjectService = Depends(get_project_service)
):
    # 判断章节内容是否存在
    chapter = chapter_service.get_chapter(chapter_id)
    if chapter.text_content is None:
        return Res(data=None, code=400, message="章节内容不存在")
    try:
        contents = chapter_service.split_text(chapter_id, 1500)
        print("内容划分为", len(contents), "段")
    except Exception as e:
        logging.error(f"章节拆分失败: {e}\n{traceback.format_exc()}")
        return Res(data=None, code=500, message="章节拆分失败")

    all_line_data = []

    try:
        roles = role_service.get_all_roles(project_id)
        roles = set(role.name for role in roles)
        emotions = emotion_service.get_all_emotions()
        strengths = strength_service.get_all_strengths()

        emotion_names = [emotion.name for emotion in emotions]
        strength_names = [strength.name for strength in strengths]
        emotions_dict = {emotion.name: emotion.id for emotion in emotions}
        strengths_dict = {strength.name: strength.id for strength in strengths}
    except Exception as e:
        logging.error(f"初始化角色/情绪/强度失败: {e}\n{traceback.format_exc()}")
        return Res(data=None, code=500, message="初始化角色/情绪/强度失败")

    project = project_service.get_project(project_id)
    # 精准填充
    is_precise_fill = project.is_precise_fill
    # 判断tts，llm，model是否存在
    if project.tts_provider_id is None or project.llm_provider_id is None or project.llm_model is None:
        return Res(data=None, code=500, message="tts/llm/model不存在")


    prompt = prompt_service.get_prompt(project.prompt_id) if project else None
    if prompt is None:
        return Res(data=None, code=500, message="提示词不存在")

    for idx, content in enumerate(contents):
        logging.info(f"解析第 {idx + 1}/{len(contents)} 段...")

        try:
            roles_list = list(roles)
            result = chapter_service.para_content(
                prompt.content, chapter_id, content,
                roles_list, emotion_names, strength_names,is_precise_fill
            )

            if not result["success"]:
                return Res(
                data=None,
                code=500,
                message=result["message"]
                )

            # 提取lines_data中的角色
            lines_data = result["data"]
            for line_data in lines_data:
                roles.add(line_data.role_name)

            all_line_data.extend(lines_data)

        except Exception as e:
            logging.error(
                f"解析第 {idx + 1} 段失败: {e}\n{traceback.format_exc()}"
            )
            return Res(data=None, code=500, message=f"解析失败：第 {idx + 1} 段处理出错，错误信息：{e}")

    try:
        audio_path = os.path.join(project.project_root_path,str(project_id),str(chapter_id),"audio")
        os.makedirs(audio_path, exist_ok=True)
        line_service.update_init_lines(
            all_line_data, project_id, chapter_id, emotions_dict, strengths_dict,audio_path
        )
    except Exception as e:
        logging.error(f"写入数据库失败: {e}\n{traceback.format_exc()}")
        return Res(data=None, code=500, message="写入数据库失败")

    return Res(data=None, code=200, message="解析成功")


# 导出LLM prompt指令
@router.get("/export-llm-prompt/{project_id}/{chapter_id}",response_model=Res[str],summary="导出LLM prompt指令",description="导出LLM prompt指令")
async def export_llm_prompt(project_id:int,chapter_id: int, chapter_service: ChapterService = Depends(get_chapter_service),
                            project_service = Depends(get_project_service),
                            prompt_service: PromptService = Depends(get_prompt_service),
                            role_service: RoleService = Depends(get_role_service),
                            emotion_service: EmotionService = Depends(get_emotion_service),
                            strength_service: StrengthService = Depends(get_strength_service)):
    try:
        roles = role_service.get_all_roles(project_id)
        roles = [role.name for role in roles]
        emotions = emotion_service.get_all_emotions()
        strengths = strength_service.get_all_strengths()

        emotion_names = [emotion.name for emotion in emotions]
        strength_names = [strength.name for strength in strengths]
    except Exception as e:
        return Res(data=None, code=500, message="初始化角色/情绪/强度失败")

    project = project_service.get_project(project_id)
    prompt = prompt_service.get_prompt(project.prompt_id) if project else None
    chapter = chapter_service.get_chapter(chapter_id)
    content = chapter.text_content
    res = chapter_service.fill_prompt(prompt.content, roles, emotion_names, strength_names, content)
    # record
    return Res(data=res, code=200, message="导出成功")

# 解析第三方的json
@router.post("/import-lines/{project_id}/{chapter_id}",response_model=Res[str],summary="导入第三方json",description="导入第三方json")
async def import_lines(project_id: int,chapter_id: int,data:str=Form( ...),line_service: LineService = Depends(get_line_service),
                       emotion_service: EmotionService = Depends(get_emotion_service),
                       strength_service: StrengthService = Depends(get_strength_service),
                       project_service: ProjectService = Depends(get_project_service),
                       chapter_service: ChapterService = Depends(get_chapter_service)):
    # 解析data
    lines_data = json.loads(data)
    # 转化成List[LineInitDTO]
    emotions = emotion_service.get_all_emotions()
    strengths = strength_service.get_all_strengths()

    emotions_dict = {emotion.name: emotion.id for emotion in emotions}
    strengths_dict = {strength.name: strength.id for strength in strengths}
    # 精准填充
    project = project_service.get_project(project_id)
    is_precise_fill = project.is_precise_fill
    
    if is_precise_fill == 1:
        # 获取章节内容
        content = chapter_service.get_chapter(chapter_id).text_content
        if not content:
            return Res(data=None, code=500, message="章节内容为空")
        corrector = TextCorrectorFinal()
        lines_data = corrector.correct_ai_text(content, lines_data)
    lines_data = [LineInitDTO(**line) for line in lines_data]


    audio_path = os.path.join(project.project_root_path,str(project_id),str(chapter_id),"audio")
    os.makedirs(audio_path, exist_ok=True)
    line_service.update_init_lines(lines_data, project_id, chapter_id, emotions_dict, strengths_dict,audio_path)
    return Res(data=None, code=200, message="导入成功")



# @router.post("/save-init-lines/{project_id}/{chapter_id}",response_model=Res[str],summary="保存初始化调整后的解析内容",description="保存初始化调整后的解析内容")
# async def update_init_lines(project_id: int,chapter_id: int,lines: List[LineInitDTO], chapter_service: ChapterService = Depends(get_chapter_service)):
#     chapter_service.update_init_lines(lines,project_id,chapter_id)
#     return Res(data=None, code=200, message="保存成功")

# 绑定音色就是采用的修改角色信息

# 获取章节下所有台词



# 传入台词实体，然后生成音频
# @router.post("/generate-audio/{project_id}/{chapter_id}",response_model=Res[str],summary="生成音频",description="生成音频")
# async def generate_audio(project_id: int,chapter_id: int,
#                          dto: LineCreateDTO, chapter_service: ChapterService = Depends(get_chapter_service),
#                          voice_service: VoiceService = Depends(get_voice_service),
#                          role_service: RoleService = Depends(get_role_service),
#                          project_service: ProjectService = Depends(get_project_service)):
#     """生成音频"""
#     # 获取角色绑定的音色的reference_path
#     role = role_service.get_role(dto.role_id)
#     voice = voice_service.get_voice(role.default_voice_id)
#     project = project_service.get_project(project_id)
#     save_path = dto.audio_path
#     res = chapter_service.generate_audio(voice.reference_path,project.tts_provider_id,dto.text_content,save_path=save_path)
#     return Res(data=None, code=200, message="生成成功")

# 合并结果并导出
# @router.get("/export-audio/{project_id}/{chapter_id}",response_model=Res[str],summary="合并结果并导出",description="合并结果并导出")
# async def export_audio(project_id: int,chapter_id: int, chapter_service: ChapterService = Depends(get_chapter_service))
#     res = chapter_service.export_audio(project_id,chapter_id)

# 添加智能匹配角色和音色的功能
@router.post("/add-smart-role-and-voice/{project_id}/{chapter_id}",response_model=Res[List],summary="添加智能匹配角色和音色的功能",description="添加智能匹配角色和音色的功能")
async def add_smart_role_and_voice(project_id: int,chapter_id: int,
                                   chapter_service: ChapterService = Depends(get_chapter_service),
                                   project_service: ProjectService = Depends(get_project_service),
                                   voice_service: VoiceService = Depends(get_voice_service),
                                   role_service: RoleService = Depends(get_role_service)):
    # 获取项目信息
    project = project_service.get_project(project_id)
    # 首先获取项目下所有角色
    roles = role_service.get_all_roles(project_id)
#     将所有角色未绑定音色的角色提取出来
    roles_no_voice = [role for role in roles if role.default_voice_id is None]
    # 只要角色name
    role_names = [role.name for role in roles_no_voice]
    # 获取所有音色
    voices = voice_service.get_all_voices(project.tts_provider_id)
    # 只要音色的名字和描述
    voice_names = [
        {
            "name": voice.name,
            "description": voice.description
        }
        for voice in voices
    ]
    # 获取原文内容
    content = chapter_service.get_chapter(chapter_id).text_content
    res,data = chapter_service.add_smart_role_and_voice(project,content,role_names,voice_names)
    # 将data中的每一个元素转化为RoleBindVoiceDTO
    # data = [RoleBindVoiceDTO(**item) for item in data]
    if res:
        return Res(data=data, code=200, message="智能匹配成功")
    else:
        return Res(data=None, code=500, message="智能匹配失败")
