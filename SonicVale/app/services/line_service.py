import contextlib
import hashlib

import shutil
import subprocess
import sys
import tempfile
import threading
from collections import defaultdict
from typing import List

from openpyxl import Workbook
from sqlalchemy import Sequence


from app.core.audio_engin import AudioProcessor
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
    def add_new_line(self, line: LineCreateDTO,project_id,chapter_id,index,emotions_dict, strengths_dict,audio_path):
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

        # audio_path = os.path.join(getConfigPath(), str(project_id), str(chapter_id), "audio")
        # os.makedirs(audio_path, exist_ok=True)
        res_path = os.path.join(audio_path, "id_"+str(res.id) + ".wav")
        self.repository.update(res.id, {"audio_path": res_path})


    def update_init_lines(self, lines: list, project_id: object, chapter_id: object,emotions_dict, strengths_dict,audio_path) -> None:
        for index, line in enumerate(lines):
            self.add_new_line(line,project_id,chapter_id,index,emotions_dict, strengths_dict,audio_path)

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


    # 删除区间进行拼接
    def process_audio_ffmpeg_cut(
            self,
            audio_path: str,
            speed: float = 1.0,
            volume: float = 1.0,
            start_ms: int | None = None,
            end_ms: int | None = None,
            silence_sec: float = 0.0,  # 末尾静音时长，单位秒
            out_path: str | None = None,
            keep_format: bool = True,  # 是否保持原文件采样率/声道
            default_sr: int = 44100,
            default_ch: int = 2
    ):
        """
        使用 ffmpeg 对音频进行变速 (0.5~2.0)、音量调整。
        删除 [start_ms, end_ms] 区间，并拼接前后音频。
        输出 WAV PCM16。
        可在末尾附加 silence_sec 秒静音。
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
        if start_ms is None or end_ms is None or end_ms <= start_ms:
            # 无剪切
            if silence_sec > 0:
                # 添加静音
                cmd = [
                    ffmpeg_path, "-y",
                    "-i", audio_path,
                    "-f", "lavfi", "-t", str(silence_sec),
                    "-i", f"anullsrc=channel_layout={'stereo' if target_ch == 2 else 'mono'}:sample_rate={target_sr}",
                    "-filter_complex",
                    f"[0:a]atempo={speed},volume={volume}[main];"
                    f"[main][1:a]concat=n=2:v=0:a=1[out]",
                    "-map", "[out]",
                    "-ar", str(target_sr),
                    "-ac", str(target_ch),
                    "-c:a", "pcm_s16le",
                    tmp_path
                ]
            elif silence_sec < 0:
                # 裁掉末尾 abs(silence_sec)
                cut_dur = info.duration + silence_sec
                if cut_dur <= 0:
                    cut_dur = 0  # 整段裁掉

                cmd = [
                    ffmpeg_path, "-y",
                    "-i", audio_path,
                    "-filter_complex",
                    f"[0:a]atempo={speed},volume={volume},atrim=0:{cut_dur}[out]",
                    "-map", "[out]",
                    "-ar", str(target_sr),
                    "-ac", str(target_ch),
                    "-c:a", "pcm_s16le",
                    tmp_path
                ]
            else:
                # 不处理末尾
                cmd = [
                    ffmpeg_path, "-y", "-i", audio_path,
                    "-af", f"atempo={speed},volume={volume}",
                    "-ar", str(target_sr),
                    "-ac", str(target_ch),
                    "-c:a", "pcm_s16le",
                    tmp_path
                ]


        else:

            # 剪切

            start_sec = start_ms / 1000

            end_sec = end_ms / 1000

            if silence_sec > 0:

                # 拼接 + 添加静音

                cmd = [

                    ffmpeg_path, "-y",

                    "-i", audio_path,

                    "-f", "lavfi", "-t", str(silence_sec),

                    "-i", f"anullsrc=channel_layout={'stereo' if target_ch == 2 else 'mono'}:sample_rate={target_sr}",

                    "-filter_complex",

                    f"[0:a]atrim=0:{start_sec},asetpts=PTS-STARTPTS[first];"

                    f"[0:a]atrim={end_sec},asetpts=PTS-STARTPTS[second];"

                    f"[first][second]concat=n=2:v=0:a=1,atempo={speed},volume={volume}[main];"

                    f"[main][1:a]concat=n=2:v=0:a=1[out]",

                    "-map", "[out]",

                    "-ar", str(target_sr),

                    "-ac", str(target_ch),

                    "-c:a", "pcm_s16le",

                    tmp_path

                ]

            elif silence_sec < 0:

                # 拼接后再裁掉末尾

                cut_dur = info.duration + silence_sec
                if cut_dur <= 0:
                    cut_dur = 0  # 整段裁掉

                cmd = [

                    ffmpeg_path, "-y", "-i", audio_path,

                    "-filter_complex",

                    f"[0:a]atrim=0:{start_sec},asetpts=PTS-STARTPTS[first];"

                    f"[0:a]atrim={end_sec},asetpts=PTS-STARTPTS[second];"

                    f"[first][second]concat=n=2:v=0:a=1,atempo={speed},volume={volume},atrim=0:{cut_dur}[out]",

                    "-map", "[out]",

                    "-ar", str(target_sr),

                    "-ac", str(target_ch),

                    "-c:a", "pcm_s16le",

                    tmp_path

                ]

            else:

                # 拼接但不处理末尾

                cmd = [

                    ffmpeg_path, "-y", "-i", audio_path,

                    "-filter_complex",

                    f"[0:a]atrim=0:{start_sec},asetpts=PTS-STARTPTS[first];"

                    f"[0:a]atrim={end_sec},asetpts=PTS-STARTPTS[second];"

                    f"[first][second]concat=n=2:v=0:a=1,atempo={speed},volume={volume}[out]",

                    "-map", "[out]",

                    "-ar", str(target_sr),

                    "-ac", str(target_ch),

                    "-c:a", "pcm_s16le",

                    tmp_path

                ]

        # 执行 ffmpeg
        subprocess.run(
            cmd, check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

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
        #     audio_file =self.process_audio_ffmpeg(line.audio_path, dto.speed, dto.volume,dto.start_ms,dto.end_ms)
        # 删除拼接
        #     audio_file = self.process_audio_ffmpeg_cut(line.audio_path, dto.speed, dto.volume, dto.start_ms, dto.end_ms, dto.tail_silence_sec,dto.current_ms)
            processor = AudioProcessor(line.audio_path)
            start_ms = dto.start_ms
            end_ms = dto.end_ms
            speed = dto.speed
            volume = dto.volume
            current_ms = dto.current_ms
            silence_sec = dto.silence_sec
            # ---------- (1) 优先裁剪 ----------
            if start_ms is not None and end_ms is not None and end_ms > start_ms:
                print("裁剪")
                processor.cut(start_ms, end_ms)

            # ---------- (2) 插入静音 ----------
            elif current_ms is not None and silence_sec is not None and silence_sec != 0:
                print("插入静音")
                processor.insert_silence(current_ms, silence_sec)

            # ---------- (3) 末尾静音/裁剪 ----------
            elif current_ms is None and silence_sec is not None and silence_sec != 0:
                print("末尾静音/裁剪")
                processor.append_silence(silence_sec)

            # ---------- (4) 音量 + 变速 ----------
            if speed != 1.0:
                processor.change_speed(speed)
            if volume != 1.0:
                processor.change_volume(volume)
            print("音频处理完成")
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



    def export_lines_to_excel(self,lines, file_path="all_lines.xlsx"):
        # 1) 取出所有数据
        # lines = self.repository.get_all(chapter_id)

        # 2) 创建 Excel 工作簿
        wb = Workbook()
        ws = wb.active
        ws.title = "Lines"

        # 3) 写表头（根据你的数据字段调整）
        headers = ["序号","角色", "台词"]
        ws.append(headers)

        # 4) 写内容
        for line in lines:
            role = self.role_repository.get_by_id(line.role_id)
            role_name = role.name if role else "未知角色"
            ws.append([
                line.line_order,
                role_name,
                line.text_content
            ])
        # 5) 保存到文件
        wb.save(file_path)
        return file_path

    def export_audio(self, chapter_id,single=False):
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


            if single:
                # 生成所有的单条字幕
                subtitle_dir_path = os.path.join(os.path.dirname(paths[0]), "subtitles")
                # 先清空这个文件夹
                shutil.rmtree(subtitle_dir_path, ignore_errors=True)
                os.makedirs(subtitle_dir_path, exist_ok=True)
                for line in lines:
                    path = line.audio_path
                    base_name = os.path.splitext(os.path.basename(path))[0]
                    subtitle_path = os.path.join(subtitle_dir_path, base_name + ".srt")
                    subtitle_engine.generate_subtitle(path,subtitle_path)
                    #     将subtitle_path写进line.subtitle_path
                    self.repository.update(line.id,{"subtitle_path":subtitle_path})
            # 导出所有数据
            self.export_lines_to_excel(lines, os.path.join(output_dir_path, "all_lines.xlsx"))
            return True
        else:
            return False



    def generate_subtitle(self, line_id, dto):
        # 获取台词
        line = self.get_line(line_id)
        if line:
            # 将音频文件路径的后缀改为.srt
            dto.subtitle_path = os.path.splitext(dto.subtitle_path)[0] + ".srt"
            subtitle_engine.generate_subtitle(line.audio_path,dto.subtitle_path)
            return dto.subtitle_path
        else:
            return None
#     字幕矫正
    def correct_subtitle(self, text, output_subtitle_path):
        subtitle_engine.correct_srt_file(text, output_subtitle_path)

#     生成字幕
#     def generate_subtitle(self, res_path):
#         subtitle_engine.generate_subtitle(res_path,res_path+".srt")
