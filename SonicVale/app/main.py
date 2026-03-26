# app/main.py
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from app.core.config import getConfigPath
from app.core.prompts import get_prompt_str
from app.core.tts_runtime import tts_worker
from app.core.ws_manager import manager
from app.db.database import Base, engine, SessionLocal, get_db
from app.entity.emotion_entity import EmotionEntity
from app.entity.strength_entity import StrengthEntity
from app.models.po import *
from app.repositories.llm_provider_repository import LLMProviderRepository
from app.repositories.tts_provider_repository import TTSProviderRepository
from app.routers import project_router, chapter_router, role_router, voice_router, llm_provider_router, \
    tts_provider_router, line_router, emotion_router, strength_router, multi_emotion_voice_router, prompt_router
from app.routers.chapter_router import get_strength_service, get_prompt_service, get_project_service
from app.routers.emotion_router import get_emotion_service
from app.routers.llm_provider_router import get_llm_service
from app.services.llm_provider_service import LLMProviderService

from app.services.tts_provider_service import TTSProviderService

import os
import sys

root_path = os.getcwd()
sys.path.append(root_path)
# =========================
# FastAPI 实例
# =========================
app = FastAPI(
    title="音墟 (YinXu) - AI多角色小说配音",
    description="桌面端小说多角色配音系统，支持 TTS、GPT 提取角色、台词管理及字幕生成",
    version="1.0.0",
)
# 跨域
# 允许的前端地址
origins = [
    "http://localhost:5173",  # Vue 开发服务器
    "http://127.0.0.1:5173"   # 有些浏览器可能会用这个
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # 允许的源
    allow_credentials=True,
    allow_methods=["*"],          # 允许所有方法（GET, POST, DELETE...）
    allow_headers=["*"],          # 允许所有请求头
)



# =========================
# 数据库初始化（创建表）
# =========================

# 启动时创建表
# @app.on_event("startup")
# def startup():
#     Base.metadata.create_all(bind=engine)

WORKERS = 1
QUEUE_CAPACITY = 0

from sqlalchemy import text

def add_prompt_id_column():
    with engine.connect() as conn:
        # 检查 project 表是否已有 prompt_id
        result = conn.execute(text("PRAGMA table_info(projects)"))
        columns = [row[1] for row in result.fetchall()]
        if "prompt_id" not in columns:
            conn.execute(text("ALTER TABLE projects ADD COLUMN prompt_id INTEGER"))
            conn.commit()

# 添加line表中is_done字段
def add_is_done_column():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(lines)"))
        columns = [row[1] for row in result.fetchall()]
        if "is_done" not in columns:
            # ✅ 添加列并设置默认值 0
            conn.execute(text("ALTER TABLE lines ADD COLUMN is_done INTEGER DEFAULT 0"))
            conn.commit()

# 添加LLM自定义参数字段
def add_custom_params_column():
    with engine.begin() as conn:  # ✅ 用 begin() 自动提交事务
        result = conn.execute(text("PRAGMA table_info(llm_provider)"))
        columns = [row[1] for row in result.fetchall()]
        if "custom_params" not in columns:
            # ✅ 添加列
            conn.execute(text("ALTER TABLE llm_provider ADD COLUMN custom_params TEXT"))

            # ✅ 可选：为历史数据填入默认 JSON（推荐）
            import json
            default_json = json.dumps({
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
                "top_p": 0.9
            }, ensure_ascii=False)
            conn.execute(
                text("UPDATE llm_provider SET custom_params = :val"),
                {"val": default_json}
            )

            logging.info("已添加 custom_params 列并写入默认值。")
        else:
            logging.info("custom_params 列已存在，跳过。")

# 添加精准填充字段】
def add_is_precise_fill_column():
    with engine.begin() as conn:  # ✅ 用 begin() 自动提交事务
        result = conn.execute(text("PRAGMA table_info(projects)"))
        columns = [row[1] for row in result.fetchall()]
        if "is_precise_fill" not in columns:
            # ✅ 添加列
            conn.execute(text("ALTER TABLE projects ADD COLUMN is_precise_fill INTEGER DEFAULT 0"))

            conn.commit()

# 添加项目保存路径字段（project_path）
def add_project_root_path_column():
    with engine.begin() as conn:  # ✅ 用 begin() 自动提交事务
        result = conn.execute(text("PRAGMA table_info(projects)"))
        columns = [row[1] for row in result.fetchall()]
        if "project_root_path" not in columns:
            # ✅ 添加列
            conn.execute(text("ALTER TABLE projects ADD COLUMN project_root_path TEXT"))

            conn.commit()

def get_tts_service(db: Session = Depends(get_db)) -> TTSProviderService:
    return TTSProviderService(TTSProviderRepository(db))

@app.on_event("startup")
async def startup_event():
    # 1) 建表
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logging.exception("❌ 数据库建表失败: %s", e)

    # 更改数据库表字段
    add_prompt_id_column()
    # v1.0.6添加字段 is_done
    add_is_done_column()
    # v1.0.7 添加字段 custom_params
    add_custom_params_column()
    # v1.0.7 添加项目的字段 is_precise_fill
    add_is_precise_fill_column()
    # v1.0.7 添加项目的字段 project_root_path
    add_project_root_path_column()

    # 2) 初始化共享运行时
    try:
        app.state.tts_queue = asyncio.Queue(maxsize=QUEUE_CAPACITY)
        app.state.tts_executor = ThreadPoolExecutor(max_workers=WORKERS)
    except Exception as e:
        logging.exception("❌ 初始化队列/线程池失败: %s", e)

    # 3) 启动后台 worker
    try:
        app.state.tts_workers = [
            asyncio.create_task(tts_worker(app)) for _ in range(WORKERS)
        ]
    except Exception as e:
        logging.exception("❌ 启动 worker 失败: %s", e)

    # 4) 初始化默认数据
    db = SessionLocal()
    try:
        try:
            tts_service = get_tts_service(db)
            tts_service.create_default_tts_provider()
        except Exception as e:
            logging.warning("⚠️ 默认 TTS provider 初始化失败: %s", e)

        try:
            emotion_service = get_emotion_service(db)
            for name in ["高兴","生气","伤心","害怕","厌恶","低落","惊喜","平静"]:
                try:
                    emotion_service.create_emotion(EmotionEntity(name=name))
                except Exception as e:
                    logging.debug("情绪 %s 已存在或创建失败: %s", name, e)
        except Exception as e:
            logging.warning("⚠️ 情绪初始化失败: %s", e)

        try:
            strength_service = get_strength_service(db)
            for name in ["微弱","稍弱","中等","较强","强烈"]:
                try:
                    strength_service.create_strength(StrengthEntity(name=name))
                except Exception as e:
                    logging.debug("强度 %s 已存在或创建失败: %s", name, e)
        except Exception as e:
            logging.warning("⚠️ 强度初始化失败: %s", e)

    #     创建默认提示词
        try:
            prompt_service = get_prompt_service(db)
            if not prompt_service.get_all_prompts():
                logging.info("创建默认提示词")
                prompt_service.create_default_prompt()
            else:
                default_prompt =  prompt_service.get_prompt_by_name("默认拆分台词提示词")
                if not default_prompt:
                    prompt_service.create_default_prompt()
                else:
                    #修改默认提示词
                    default_prompt_content = get_prompt_str()
                    default_prompt.content = default_prompt_content
                    prompt_service.update_prompt(default_prompt.id, default_prompt.__dict__)

        except Exception as e:
            logging.warning("⚠️ 默认提示词创建失败: %s", e)
    # 兼容之前版本，已有的项目的project_root_path 为 getConfigPath()
        try:
            project_service = get_project_service(db)
            for project in project_service.get_all_projects():
                if not project.project_root_path:
                    project.project_root_path = getConfigPath()
                    project_service.update_project(project.id, project.__dict__)
                    logging.info("项目 %s 默认项目路径已修改为 %s", project.name, project.project_root_path)

        #             todo:修改所有的保存路径，然后前端请求添加保存路径（利用electron读取文件夹路径）
        except Exception as e:
            logging.warning("⚠️ 项目默认项目路径初始化失败: %s", e)

    except Exception as e:
        logging.exception("❌ 默认数据初始化异常: %s", e)
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    # 优雅退出
    for t in getattr(app.state, "tts_workers", []):
        t.cancel()
    ex = getattr(app.state, "tts_executor", None)
    if ex:
        ex.shutdown(wait=False, cancel_futures=True)
# =========================
# 注册路由
# =========================
app.include_router(project_router.router)
app.include_router(chapter_router.router)
app.include_router(role_router.router)
app.include_router(voice_router.router)
app.include_router(llm_provider_router.router)
app.include_router(tts_provider_router.router)
app.include_router(line_router.router)
app.include_router(emotion_router.router)
app.include_router(strength_router.router)
app.include_router(multi_emotion_voice_router.router)
app.include_router(prompt_router.router)
# =========================
# 健康检查接口
# =========================
@app.get("/")
def read_root():
    return {"msg": "音墟 (YinXu) 后端服务运行中！"}

# =========================
# 小测试接口：插入并查询 ProjectPO
# =========================
@app.get("/test-db")
def test_db():
    session: Session = SessionLocal()
    try:
        # 使用时间戳生成唯一名称，避免 UNIQUE 冲突
        name = f"测试项目_{int(datetime.now().timestamp())}"

        test_project = ProjectPO(name=name, description="测试用项目")
        session.add(test_project)
        session.commit()
        session.refresh(test_project)

        return {
            "msg": "插入成功",
            "id": test_project.id,
            "name": test_project.name,
            "created_at": test_project.created_at,
            "updated_at": test_project.updated_at
        }

    except Exception as e:
        session.rollback()
        return {"error": str(e)}

    finally:
        session.close()


import json
from fastapi import WebSocket

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            msg_text = await ws.receive_text()
            try:
                data = json.loads(msg_text)
            except:
                data = {}

            # 👇 心跳处理：收到 ping 立即回复 pong
            if data.get("type") == "ping":
                logging.debug("receive ping")
                await ws.send_text(json.dumps({"type": "pong"}))
                continue

            # 这里可以扩展处理订阅/其他消息

    except:
        manager.disconnect(ws)



if __name__ == "__main__":

    # uvicorn.run(app, host="127.0.0.1", port=8200)
    # 使用自定义 logger，避免 uvicorn 自动配置失败
    # logging.basicConfig(level=logging.INFO)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8200, log_config=None)
