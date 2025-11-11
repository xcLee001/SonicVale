import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Request, Query
from sqlalchemy.orm import Session

from app.core.config import getConfigPath
from app.core.response import Res
from app.core.ws_manager import manager
from app.db.database import get_db, SessionLocal
from app.dto.line_dto import LineResponseDTO, LineCreateDTO, LineOrderDTO, LineAudioProcessDTO
from app.entity.line_entity import LineEntity
from app.repositories.chapter_repository import ChapterRepository
from app.repositories.llm_provider_repository import LLMProviderRepository
from app.repositories.multi_emotion_voice_repository import MultiEmotionVoiceRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.line_repository import LineRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.tts_provider_repository import TTSProviderRepository
from app.repositories.voice_repository import VoiceRepository
from app.services.chapter_service import ChapterService
from app.services.project_service import ProjectService
from app.services.line_service import LineService
from app.services.role_service import RoleService
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/lines", tags=["Lines"])


# 依赖注入（实际项目可用 DI 容器）

def get_line_service(db: Session = Depends(get_db)) -> LineService:
    repository = LineRepository(db)
    role_repository = RoleRepository(db)
    tts_repository = TTSProviderRepository(db)
    return LineService(repository,role_repository,tts_repository)
def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    repository = ProjectRepository(db)
    return ProjectService(repository)

def get_chapter_service(db: Session = Depends(get_db)) -> ChapterService:
    repository = ChapterRepository(db)
    return ChapterService(repository)

def get_voice_service(db: Session = Depends(get_db)) -> VoiceService:
    repository = VoiceRepository(db)
    multi_emotion_voice_repository = MultiEmotionVoiceRepository(db)
    return VoiceService(repository, multi_emotion_voice_repository)

def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    repository = RoleRepository(db)
    return RoleService(repository)
@router.post("/{project_id}", response_model=Res[LineResponseDTO],
             summary="创建台词",
             description="根据项目ID创建台词" )
def create_line(project_id:int,dto: LineCreateDTO, line_service: LineService = Depends(get_line_service),
                   project_service: ProjectService = Depends(get_project_service),
                    chapter_service : ChapterService = Depends(get_chapter_service)):
    """创建台词"""
    try:
        # DTO → Entity
        entity = LineEntity(**dto.__dict__)
        # 判断project_id是否存在
        project = project_service.get_project(project_id)
        if project is None:
            return Res(data=None, code=400, message=f"项目 '{project_id}' 不存在")

        chapter = chapter_service.get_chapter(dto.chapter_id)
        if chapter is None:
            return Res(data=None, code=400, message=f"章节 '{dto.chapter_id}' 不存在")
        # 调用 Service 创建项目（返回 True/False）

        entityRes = line_service.create_line(entity)

        # 新增台词,这里搞个audio_path
        audio_path = os.path.join(project.project_root_path, str(project_id), str(dto.chapter_id), "audio")
        os.makedirs(audio_path, exist_ok=True)
        res_path = os.path.join(audio_path, "id_" + str(entityRes.id) + ".wav")
        line_service.update_line(entityRes.id, {"audio_path": res_path})

        # 返回统一 Response
        if entityRes is not None:
            # 创建成功，可以返回 DTO 或者部分字段
            res = LineResponseDTO(**entityRes.__dict__)
            return Res(data=res, code=200, message="创建成功")
        else:
            return Res(data=None, code=400, message=f"台词 '{entity.name}' 已存在")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{line_id}", response_model=Res[LineResponseDTO],
            summary="查询台词",
            description="根据台词id查询台词信息")
def get_line(line_id: int, line_service: LineService = Depends(get_line_service)):
    entity = line_service.get_line(line_id)
    if entity:
        res = LineResponseDTO(**entity.__dict__)
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=None, code=404, message="项目不存在")

@router.get("/lines/{chapter_id}", response_model=Res[List[LineResponseDTO]],
            summary="查询章节下的所有台词",
            description="根据章节id查询章节下的所有台词信息")
def get_all_lines(chapter_id: int, line_service: LineService = Depends(get_line_service)):
    entities = line_service.get_all_lines(chapter_id)
    if entities:
        res = [LineResponseDTO(**e.__dict__) for e in entities]
        return Res(data=res, code=200, message="查询成功")
    else:
        return Res(data=[], code=200, message="章节不存在台词")

# 修改，传入的参数是id
@router.put("/{line_id}", response_model=Res[LineCreateDTO],
            summary="修改台词信息",
            description="根据台词id修改台词信息,并且不能修改章节id")
def update_line(line_id: int, dto: LineCreateDTO, line_service: LineService = Depends(get_line_service)):
    line = line_service.get_line(line_id)
    if line is None:
        return Res(data=None, code=404, message="台词不存在")
    res = line_service.update_line(line_id, dto.dict(exclude_unset=True))
    if res:
        return Res(data=dto, code=200, message="修改成功")
    else:
        return Res(data=None, code=400, message="修改失败")


# 根据id，删除
@router.delete("/{line_id}", response_model=Res,
               summary="删除台词",
               description="根据台词id删除台词信息")
def delete_line(line_id: int, line_service: LineService = Depends(get_line_service)):
    success = line_service.delete_line(line_id)
    if success:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败或台词不存在")

# 删除章节下所有台词
@router.delete("/lines/{chapter_id}", response_model=Res,summary="删除章节下所有台词",description="根据章节id删除章节下的所有台词信息")
def delete_all_lines(chapter_id: int, line_service: LineService = Depends(get_line_service)):
    success = line_service.delete_all_lines(chapter_id)
    if success:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="删除失败或台词不存在")





@router.put("/batch/orders", response_model=Res[bool])
def batch_update_line_order(
    line_orders: List[LineOrderDTO] = Body(...),  # 关键：明确从 body 读取“数组”
    line_service: LineService = Depends(get_line_service),
):
    res = line_service.batch_update_line_order(line_orders)
    return Res(data=res, code=200, message="更新成功")

# 完成配音时候，更新音频路径，保证顺序一致
@router.put("/{line_id}/audio_path", response_model=Res[bool])
def update_line_audio_path(
        line_id: int,
    dto: LineCreateDTO,  # 关键：明确从 body 读取“数组”
    line_service: LineService = Depends(get_line_service),
):
    res = line_service.update_audio_path(line_id,dto)
    if not res:
        return Res(data=None, code=400, message="更新失败")
    return Res(data=res, code=200, message="更新成功")



@router.post("/generate-audio/{project_id}/{chapter_id}")
def generate_audio(request: Request, project_id: int, dto: LineCreateDTO,line_service: LineService = Depends(get_line_service)):
    q = request.app.state.tts_queue  # 👈 永远拿到已初始化的同一份队列
    if q.full():
        # 可选：带上 Retry-After 头
        raise HTTPException(status_code=429, detail="队列已满，请稍后重试")
    q.put_nowait((project_id, dto))
    #
    line_service.update_line(dto.id, {"status": "processing"})
    # manager.broadcast({
    #     "event": "line_update",
    #     "line_id": dto.id,
    #     "status": "processing",
    #     "progress":  q.qsize(),
    #     "meta": f"角色 {dto.role_id} 开始生成"
    # })
    print("队列剩余数量:", q.qsize())
    return {"code": 200, "message": "已入队", "data": {"line_id": dto.id}}


# 改为异步任务

# @router.post("/generate-audio/{project_id}/{chapter_id}")
# async def generate_audio(project_id : int, chapter_id: int, dto: LineCreateDTO):
#     # 立即返回，不阻塞
#     asyncio.create_task(_run_line_tts(project_id,dto))
#     return {"code": 200, "message": "已入队", "data": {"line_id": dto.id}}
#
#
# TTS_EXECUTOR = ThreadPoolExecutor(max_workers=4)  # 线程池大小
# TTS_SEMAPHORE = asyncio.Semaphore(1)              # 最多 4 个并行 TTS
# async def _run_line_tts(project_id:int,dto: LineCreateDTO):
#     db = SessionLocal()
#     line_service = get_line_service(db)
#     role_service = get_role_service( db)
#     voice_service = get_voice_service(db)
#     project_service = get_project_service(db)
#     try:
#         # 1) 更新为 running
#         line_service.update_line(dto.id, {"status": "processing"})
#         print("开始生成")
#         await manager.broadcast({
#             "event": "line_update",
#             "line_id": dto.id,
#             "status": "processing",
#             "progress": 0,
#             "meta": f"角色 {dto.role_id} 开始生成"
#         })
#
#         # 2) 模拟进度
#         # 获取角色绑定的音色的reference_path
#         role = role_service.get_role(dto.role_id)
#         voice = voice_service.get_voice(role.default_voice_id)
#         project = project_service.get_project(project_id)
#         save_path = dto.audio_path
#         loop = asyncio.get_running_loop()
#         async with TTS_SEMAPHORE:
#             # 可选：设置超时，防挂死
#             try:
#                 res = await asyncio.wait_for(
#                     loop.run_in_executor(
#                         TTS_EXECUTOR,                 # ✅ 用自建线程池
#                         line_service.generate_audio,
#                         voice.reference_path,
#                         project.tts_provider_id,      # 若引擎需要 base_url，就换成 project.tts_base_url
#                         dto.text_content,
#                         save_path
#                     ),
#                     timeout=120  # 例：最多等 5 分钟
#                 )
#             except asyncio.TimeoutError:
#                 raise RuntimeError("TTS 超时")
#
#         # res = chapter_service.generate_audio(voice.reference_path,project.tts_provider_id,dto.text_content,save_path=save_path)
#         # 3) 真正合成
#         line_service.update_line(dto.id, {"status": "done"})
#
#         # 4) 广播完成
#         await manager.broadcast({
#             "event": "line_update",
#             "line_id": dto.id,
#             "status": "done",
#             "progress": 100,
#             "meta": "生成完成",
#             "audio_path": dto.audio_path
#         })
#     except Exception as e:
#         line_service.update_line(dto.id, {"status": "failed"})
#         await manager.broadcast({
#             "event": "line_update",
#             "line_id": dto.id,
#             "status": "failed",
#             "progress": 0,
#             "meta": f"失败: {e}"
#         })
#     finally:
#         db.close()
#
#
# # 批量更新line_order

# 处理音频文件，传入倍速，音量大小，以及line_id
@router.post("/process-audio/{line_id}")
async def process_audio(line_id: int, dto: LineAudioProcessDTO, line_service: LineService = Depends(get_line_service)):
    res = line_service.process_audio(line_id,dto)
    if not res:
        return Res(data=None, code=400, message="处理失败")
    return Res(data=res, code=200, message="处理成功")

# 导出音频与字幕
@router.get("/export-audio/{chapter_id}")
async def export_audio(chapter_id: int,
                       single: bool = Query(False, description="是否导出单条音频字幕"),
                       line_service: LineService = Depends(get_line_service)):
    res = line_service.export_audio(chapter_id, single)
    if not res:
        return Res(data=None, code=400, message="导出失败")
    return Res(data=res, code=200, message="导出成功")


# 生成单条音频的字幕（已经有音频）
#

# 矫正字幕
@router.post("/correct-subtitle/{chapter_id}")
async def correct_subtitle(chapter_id: int, line_service: LineService = Depends(get_line_service)):
    # res = line_service.correct_subtitle(chapter_id)

    lines = line_service.get_all_lines(chapter_id)
    if not lines:
        print("无台词记录")
        return Res(data=None, code=400, message="无台词记录")
    paths = [line.audio_path for line in lines]
    if not paths or not paths[0]:
        print("未找到有效音频路径")
        return Res(data=None, code=400, message="未找到有效音频路径")
    # 读取所有台词，组成一个文本
    text = "\n".join([line.text_content for line in lines])
    output_dir_path = os.path.join(os.path.dirname(paths[0]), "result")
    output_subtitle_path = os.path.join(output_dir_path, "result.srt")
    if os.path.exists(output_subtitle_path):
        line_service.correct_subtitle(text, output_subtitle_path)
        print("整体字幕矫正完成")
    else:
        print("请先导出音频")
        return Res(data=None, code=400, message="请先导出音频")

    #         将单条字幕也进行矫正
    print("开始对单条字幕进行矫正")
    for line in lines:
        subtitle_path = line.subtitle_path
        line_text = line.text_content
        if subtitle_path is not None and line_text is not None and os.path.exists(subtitle_path):
            line_service.correct_subtitle(line_text, subtitle_path)
            print(f"单条字幕矫正完成：{line.id}")
    return Res(data=None, code=200, message="生成成功")

