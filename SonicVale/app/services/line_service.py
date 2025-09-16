import contextlib
import hashlib

import shutil
import subprocess
import sys
import tempfile
import threading
from collections import defaultdict
from typing import List


from sqlalchemy import Sequence


from app.core.config import getConfigPath, getFfmpegPath
from app.core.subtitle import subtitle_engine
from app.core.tts_engine import TTSEngine
from app.dto.line_dto import LineCreateDTO, LineOrderDTO, LineAudioProcessDTO
from app.entity.line_entity import LineEntity
from app.models.po import LinePO, RolePO
from app.repositories.line_repository import LineRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.tts_provider_repository import TTSProviderRepository

import os

import numpy as np
import soundfile as sf

def _lock_key(path: str) -> str:
    return hashlib.md5(path.encode("utf-8")).hexdigest()
_file_locks = defaultdict(threading.Lock)
class LineService:

    def __init__(self, repository: LineRepository,role_repository: RoleRepository,tts_provider_repository: TTSProviderRepository):
        """注入 repository"""

        self.tts_provider_repository = tts_provider_repository
        self.role_repository = role_repository
        self.repository = repository

    def create_line(self,  entity: LineEntity):
        """创建新台词
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """
        # 手动将entity转化为po
        po = LinePO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = LineEntity(**data)

        # 将po转化为entity
        return entity


    def get_line(self, line_id: int) -> LineEntity | None:
        """根据 ID 查询台词"""
        po = self.repository.get_by_id(line_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = LineEntity(**data)
        return res

    def get_all_lines(self,chapter_id: int) -> Sequence[LineEntity]:
        """获取所有台词列表"""
        pos = self.repository.get_all(chapter_id)
        # pos -> entities

        entities = [
            LineEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def delete_line(self, line_id: int) -> bool:
        """删除台词
        """
        # 还要把audio_path删除
        po = self.repository.get_by_id(line_id)
        if po and po.audio_path:
            with contextlib.suppress(FileNotFoundError):
                os.remove(po.audio_path)
        res = self.repository.delete(line_id)
        return res
    # 删除章节下所有台词
    def delete_all_lines(self, chapter_id: int) -> bool:
        """删除章节下所有台词
        """
        # 要移除所有的音频资源
        for line in self.get_all_lines(chapter_id):
            if line and line.audio_path:
                with contextlib.suppress(FileNotFoundError):
                    os.remove(line.audio_path)
        return self.repository.delete_all_by_chapter_id(chapter_id)

    # 单个台词新增
    def add_new_line(self, line: LineCreateDTO,project_id,chapter_id,index,emotions_dict, strengths_dict):
    #     先判断角色是否存在
        role = self.role_repository.get_by_name(line.role_name,project_id)
        if role is None:
            #         新增角色
            role = self.role_repository.create(RolePO(name=line.role_name, project_id=project_id))
        # 获取情绪id
        emotion_id = emotions_dict.get(line.emotion_name)
        # 获取强度id
        strength_id = strengths_dict.get(line.strength_name)
        res = self.repository.create(LinePO(text_content=line.text_content, role_id=role.id,
                                           chapter_id=chapter_id,line_order = index+1,emotion_id=emotion_id,strength_id=strength_id))

        # 新增台词,这里搞个audio_path
        audio_path = os.path.join(getConfigPath(), str(project_id), str(chapter_id), "audio")
        os.makedirs(audio_path, exist_ok=True)
        res_path = os.path.join(audio_path, "id_"+str(res.id) + ".wav")
        self.repository.update(res.id, {"audio_path": res_path})


    def update_init_lines(self, lines: list, project_id: object, chapter_id: object,emotions_dict, strengths_dict) -> None:
        for index, line in enumerate(lines):
            self.add_new_line(line,project_id,chapter_id,index,emotions_dict, strengths_dict)

    # 获取章节下所有台词

    # 更新line
    def update_line(self, line_id: int, data: dict) -> bool:
        po = self.repository.get_by_id(line_id)
        if po is None:
            return False
        res = self.repository.update(line_id, data)
        if res is None:
            return False
        return True
    # 生成音频（服务器和本地两种方式）

    def generate_audio(self, reference_path: str,tts_provider_id,content,emo_text:str,emo_vector:list[float],save_path= None):
        #
        tts_provider = self.tts_provider_repository.get_by_id(tts_provider_id)
        tts_engine = TTSEngine(tts_provider.api_base_url)
        # 先判断是否存在


        # if not tts_engine.check_audio_exists(filename):
        #     # 不存在就先上传
        #     tts_engine.upload_audio(reference_path)
        # return tts_engine.synthesize(content, filename,save_path)
        key = _lock_key(reference_path)
        lock = _file_locks[key]

        with lock:
            if not tts_engine.check_audio_exists(reference_path):
                tts_engine.upload_audio(reference_path,reference_path)
            #     添加emo_text
            return tts_engine.synthesize(content, reference_path,emo_text, emo_vector,save_path)

    # 将角色role_id下所有台词的role_id都置位空
    def clear_role_id(self, role_id: int):
        # 先获取role_id下所有台词实体
        pos = self.repository.get_lines_by_role_id(role_id)
        for po in pos:
            self.repository.update(po.id, {"role_id": None})

    def batch_update_line_order(self,line_orders:List[LineOrderDTO]):
        for line_order in line_orders:
            self.update_line(line_order.id,{"line_order":line_order.line_order})
        return True

    def update_audio_path(self, id, dto) -> bool:
        try:
            po = self.get_line(id)
            old_path = po.audio_path
            new_path = dto.audio_path

            if not old_path:
                return False  # 原始路径为空

            if not os.path.exists(old_path):
                return False  # 原始文件不存在

            if os.path.exists(new_path):
                return False  # 目标文件已存在，避免覆盖

            # 确保目标目录存在
            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            # 重命名文件
            shutil.move(old_path, new_path)

            # 更新数据库
            self.update_line(id, {"audio_path": new_path})
            return True

        except Exception as e:
            # 可选：记录日志
            print(f"[update_audio_path] 失败: {e}")
            return False

    # 处理音频 文件(变速有问题。。。。。。后面重新改)
    # def process_audio_file_pitch_preserve(
    #         self,
    #         audio_path: str,
    #         speed: float = 1.0,
    #         volume: float = 1.0,
    #         start_ms: int | None = None,
    #         end_ms: int | None = None,
    #         out_path: str | None = None,
    #         normalize_if_clipping: bool = True,
    #         volume_ui_0_2: bool = False,  # 前端 0~2 滑块时设 True
    # ):
    #     """
    #     简化版：忽略 speed（不做变速/变调），仅按需裁剪 + 音量 + 限幅，然后写回。
    #     其余参数保留以兼容调用方，但不参与处理。
    #     """
    #     import os, tempfile
    #     import numpy as np
    #     import soundfile as sf
    #
    #     if not os.path.exists(audio_path):
    #         raise FileNotFoundError(audio_path)
    #
    #     # -------- 参数规整（速度被忽略，但做个基本夹紧以避免非法值传入）--------
    #     _speed = float(speed or 1.0)
    #     _speed = float(np.clip(_speed, 0.25, 4.0))  # 仅保障范围，本实现不使用
    #
    #     volume = 1.0 if volume is None else float(volume)
    #     if volume < 0:
    #         raise ValueError("volume must be >= 0")
    #     # 若前端滑块是 0~2，此处与前端 setVolume(vol/2) 对齐
    #     gain_user = (volume / 2.0) if volume_ui_0_2 else volume
    #
    #     # -------- 读取（保留多声道）--------
    #     data, sr = sf.read(audio_path, dtype="float32", always_2d=True)  # (n, ch)
    #     if data.size == 0:
    #         target_path = out_path or audio_path
    #         os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
    #         sf.write(target_path, data, sr, format="WAV", subtype="PCM_16")
    #         return target_path
    #
    #     n, ch = data.shape
    #
    #     # -------- （可选）裁剪（基于原始时间线）--------
    #     def ms_to_idx(ms: int) -> int:
    #         return int(round(ms * sr / 1000.0))
    #
    #     if start_ms is not None and end_ms is not None and end_ms > start_ms:
    #         s = max(0, ms_to_idx(int(start_ms)))
    #         e = min(n, ms_to_idx(int(end_ms)))
    #         if e - s > 1:
    #             data = data[s:e, :]
    #             n = data.shape[0]
    #
    #     # -------- 响度基线（仅记录；不做拉伸则不做 lufs 补偿）--------
    #     # （如果后续你想在“只调音量”时也做响度校正，可在此启用，但通常不需要）
    #     # def rms(x: np.ndarray) -> float:
    #     #     return float(np.sqrt(np.mean(np.square(x), dtype=np.float64))) if x.size else 0.0
    #     # rms_in = rms(data)
    #
    #     # -------- 不做任何速度相关处理（忽略 speed）--------
    #     sr_out = sr
    #     # data 时间轴保持不变
    #
    #     # -------- 用户音量 --------
    #     if abs(gain_user - 1.0) > 1e-6:
    #         data = data * gain_user
    #
    #     # -------- 软限幅 / 防削顶 --------
    #     if normalize_if_clipping and data.size:
    #         peak = float(np.max(np.abs(data)))
    #         if peak > 1.0:
    #             # 简单做整体归一；如果你偏好软限幅，可改为 tanh 柔限：
    #             # k = 2.5; x = data / peak; data = (np.tanh(k*x) / np.tanh(k)) * 0.98
    #             data = data / peak
    #
    #     # -------- 写回（原子替换）--------
    #     target_path = out_path or audio_path
    #     os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
    #     tmp_dir = os.path.dirname(target_path) or "."
    #     with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=tmp_dir) as tmp:
    #         tmp_path = tmp.name
    #     try:
    #         sf.write(tmp_path, data.astype(np.float32, copy=False), sr_out, format="WAV", subtype="PCM_16")
    #         os.replace(tmp_path, target_path)
    #     finally:
    #         try:
    #             os.remove(tmp_path)
    #         except OSError:
    #             pass
    #
    #     return target_path

    def process_audio_ffmpeg(
            self,
            audio_path: str,
            speed: float = 1.0,
            volume: float = 1.0,
            start_ms: int | None = None,
            end_ms: int | None = None,
            out_path: str | None = None,
            keep_format: bool = True,  # 是否保持原文件采样率/声道
            default_sr: int = 44100,
            default_ch: int = 2
    ):
        """
        使用 ffmpeg 对音频进行变速 (0.5~2.0)、音量调整、可选裁剪。
        输出 WAV PCM16。
        如果 keep_format=True，则保持输入文件的 sr/ch 不变。
        """
        ffmpeg_path = getFfmpegPath()
        if not os.path.exists(audio_path):
            raise FileNotFoundError(audio_path)

        # 获取原始参数
        info = sf.info(audio_path)
        target_sr = info.samplerate if keep_format else default_sr
        target_ch = info.channels if keep_format else default_ch

        # 参数规整
        speed = float(np.clip(speed or 1.0, 0.5, 2.0))
        volume = 1.0 if volume is None else max(0.0, float(volume))

        # 输出路径
        target_path = out_path or audio_path
        os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav",
                                         dir=os.path.dirname(target_path) or ".") as tmp:
            tmp_path = tmp.name

        # 构建 ffmpeg 命令
        filter_chain = [f"atempo={speed}"]
        if abs(volume - 1.0) > 1e-6:
            filter_chain.append(f"volume={volume}")

        cmd = [ffmpeg_path, "-y"]
        if start_ms is not None:
            cmd.extend(["-ss", str(start_ms / 1000)])
        cmd.extend(["-i", audio_path])
        if end_ms is not None:
            cmd.extend(["-to", str(end_ms / 1000)])
        cmd.extend([
            "-af", ",".join(filter_chain),
            "-ar", str(target_sr),
            "-ac", str(target_ch),
            "-c:a", "pcm_s16le",
            tmp_path
        ])

        subprocess.run(cmd, check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)

        # 软限幅：避免 clipping
        data, sr = sf.read(tmp_path, dtype="float32", always_2d=True)
        peak = float(np.max(np.abs(data)))
        if peak > 1.0:
            data = data / peak
            sf.write(tmp_path, data, sr, format="WAV", subtype="PCM_16")

        os.replace(tmp_path, target_path)
        return target_path

    def process_audio(self, line_id, dto:LineAudioProcessDTO):
        line = self.get_line(line_id)
        if line:
        #     读取音频文件
            audio_file =self.process_audio_ffmpeg(line.audio_path, dto.speed, dto.volume,dto.start_ms,dto.end_ms)
            return True
        else:
            return False

    # 导出音频,合并音频，并且导出字幕
    def concat_wav_files(self,paths, out_path, verify=True, block_frames=262144):
        """
        按顺序把若干 WAV 合并到 out_path。
        假设：采样率与声道一致（如需更稳，可保留 verify=True 做轻校验）。
        """
        assert paths and len(paths) >= 1, "至少提供一个文件路径"
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

        # 以首文件格式为准
        info0 = sf.info(paths[0])
        sr, ch, subtype = info0.samplerate, info0.channels, info0.subtype or "PCM_16"

        # 可选校验
        if verify:
            for p in paths[1:]:
                info = sf.info(p)
                if info.samplerate != sr or info.channels != ch:
                    raise ValueError(
                        f"格式不一致：{p} (sr={info.samplerate}, ch={info.channels}) vs 首文件 (sr={sr}, ch={ch})")

        # 流式写入
        with sf.SoundFile(out_path, mode='w', samplerate=sr, channels=ch, format='WAV', subtype=subtype) as fout:
            for p in paths:
                with sf.SoundFile(p, mode='r') as fin:
                    if verify and (fin.samplerate != sr or fin.channels != ch):
                        raise ValueError(f"参数不一致：{p}")
                    while True:
                        block = fin.read(block_frames, dtype='float32', always_2d=True)
                        if len(block) == 0:
                            break
                        fout.write(block.astype(np.float32, copy=False))
        return out_path
    def export_audio(self, chapter_id):
        # 拿到所有的台词
        lines = self.repository.get_all(chapter_id)
        paths = [line.audio_path for line in lines]
        if len(paths) > 0:
            # 把paths[0]的path去掉后面的文件名，得到文件夹路径
            output_dir_path = os.path.join(os.path.dirname(paths[0]), "result")
            # 不存在就创建
            os.makedirs(output_dir_path, exist_ok=True)
            # 放到result目录下，名字叫项目名称_章节名称.wav
            output_path = os.path.join(output_dir_path, "result.wav")
            self.concat_wav_files(paths, output_path)
            # 生成字幕
            output_subtitle_path = os.path.join(output_dir_path, "result.srt")
            subtitle_engine.generate_subtitle(output_path,output_subtitle_path)
            return True
        else:
            return False

#     生成字幕
#     def generate_subtitle(self, res_path):
#         subtitle_engine.generate_subtitle(res_path,res_path+".srt")
