
from sqlalchemy import Column, Integer, Integer, String, Text, Enum, ForeignKey, DateTime, JSON, Index
from datetime import datetime, timezone

from app.db.database import Base


# ------------------------------
# 1. 项目表 projects
# ------------------------------
class ProjectPO(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True,index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    llm_provider_id = Column(Integer, nullable=True)  # LLM提供商
    llm_model = Column(String(255), nullable=True)  # 指定模型
    tts_provider_id = Column(Integer, nullable=True)  # TTS提供商
    prompt_id = Column(Integer, nullable=True) # 关联的prompt
    # 是否开启精准填充
    is_precise_fill = Column(Integer, default=0, nullable=False)
    # 项目根地址
    project_root_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


# ------------------------------
# 2. 项目的全局角色表 roles
# ------------------------------
class RolePO(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True,index=True)
    project_id = Column(Integer,  nullable=False)
    name = Column(String(100), nullable=False)
    default_voice_id = Column(Integer, ForeignKey("voices.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


# ------------------------------
# 3. 音色表 voices
# ------------------------------
class VoicePO(Base):
    __tablename__ = "voices"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    tts_provider_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    reference_path = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    # 是否包含多情绪
    is_multi_emotion = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
                        nullable=False)

# 多情绪表
class MultiEmotionVoicePO(Base):
    __tablename__ = "multi_emotion"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    voice_id = Column(Integer, nullable=False)
    emotion_id = Column(Integer, nullable=False)
    strength_id = Column(Integer, nullable=True)
    reference_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
                        nullable=False)

# ------------------------------
# 4. 章节表 chapters
# ------------------------------
class ChapterPO(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, autoincrement=True,index=True)
    project_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=True)
    text_content = Column(Text, nullable=True)  # SQLite 没有 LongText，用 Text 替代
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
                        nullable=False)



# ------------------------------
# 5. 台词表 lines
# ------------------------------
# 情绪枚举表
class EmotionPO(Base):
    __tablename__ = "emotions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now())

# 情绪强弱枚举表
class StrengthPO(Base):
    __tablename__ = "strengths"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now())


class LinePO(Base):
    __tablename__ = "lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 外键
    chapter_id = Column(Integer, nullable=False, index=True)
    role_id = Column(Integer, nullable=True)
    voice_id = Column(Integer,  nullable=True)

    # 核心信息
    line_order = Column(Integer, nullable=True, index=True)
    text_content = Column(Text, nullable=True)
    # 情绪 和 强弱
    emotion_id = Column(Integer, nullable=True)
    strength_id = Column(Integer, nullable=True)

    # 9.1 新增


    # 输出资源
    audio_path = Column(String(500), nullable=True)
    subtitle_path = Column(String(500), nullable=True)

    # 间隔停留时间（秒）
    # wait_time = Column(Integer, default=0, nullable=True)

    # 状态
    status = Column(
        Enum("pending", "processing", "done", "failed", name="line_status"),
        default="pending",
        nullable=False
    )
    # 是否完成
    is_done = Column(Integer, default=0, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    __table_args__ = (
        Index("idx_chapter_order", "chapter_id", "line_order"),
    )

# -------------------------
# LLMProviderPO
# -------------------------
class LLMProviderPO(Base):
    __tablename__ = "llm_provider"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)           # 提供商名称
    api_base_url = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=True)                      # 可加密存储
    model_list = Column(JSON, nullable=True)                           # 支持的模型列表
    status = Column(Integer, default=1, nullable=False)               # 启用/禁用

    # ✅ 自定义参数（默认包含 response_format、temperature、top_p）
    custom_params = Column(
        Text,
        nullable=False,
        default=lambda: {
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "top_p": 0.9

        }
    )
    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
                        nullable=False)


# -------------------------
# TTSProviderPO
# -------------------------
class TTSProviderPO(Base):
    __tablename__ = "tts_provider"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    api_base_url = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=True)
    # voice_list = Column(JSON, nullable=True)
    status = Column(Integer, default=1, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
                        nullable=False)


class PromptPO(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    task = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),nullable=False)


# -------------------------
# ProjectSettings
# -------------------------
# class ProjectSettings(Base):
#     __tablename__ = "project_settings"
#
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     project_id = Column(Integer, nullable=False)                  # 所属项目
#     llm_provider_id = Column(Integer, nullable=True)              # LLM提供商
#     llm_model = Column(String(255), nullable=True)                   # 指定模型
#     tts_provider_id = Column(Integer, nullable=True)              # TTS提供商
#
#     # 时间戳
#     created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
#     updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc),
#                         nullable=False)
