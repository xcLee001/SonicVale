from app.core.subtitle.BcutASR import BcutASR
from app.core.subtitle.JianYingASR import JianYingASR
from app.core.prompts import get_subtitle_correction_prompt
from app.core.llm_engine import LLMEngine


def generate_subtitle(audio_file,save_path):
    # asr = JianYingASR(audio_file)
    asr = BcutASR(audio_file)
    result = asr.run()
    result.to_srt(save_path)
    return result



# 字幕矫正
import re
import difflib
import shutil
import logging
from pypinyin import lazy_pinyin

# -------------------- 基础工具 --------------------

def is_same_char(c1: str, c2: str) -> bool:
    """字面相同或拼音相同（处理同音字）"""
    if c1 == c2:
        return True
    return lazy_pinyin(c1) == lazy_pinyin(c2)

def correct_text_with_pinyin(original: str, recognized: str) -> str:
    """全局文本纠正：把 recognized 纠正到 original"""
    sm = difflib.SequenceMatcher(None, recognized, original, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append(recognized[i1:i2])
        else:
            r = recognized[i1:i2]
            o = original[j1:j2]
            seg = []
            L = max(len(r), len(o))
            for k in range(L):
                c1 = r[k] if k < len(r) else ""
                c2 = o[k] if k < len(o) else ""
                if c1 and c2 and is_same_char(c1, c2):
                    seg.append(c2)
                elif c2:
                    seg.append(c2)
            out.append("".join(seg))
    return "".join(out)

# -------------------- SRT 读写 --------------------

SRT_BLOCK = re.compile(
    r"(\d+)\s+([\d:,]+ --> [\d:,]+)\s+([\s\S]*?)(?=\n\n|\Z)", re.MULTILINE
)

def read_srt(path: str):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = SRT_BLOCK.findall(content)
    entries = []
    for idx, ts, txt in blocks:
        text_raw = txt.strip("\r\n")
        entries.append((int(idx), ts, text_raw))
    return entries

def write_srt(path: str, entries):
    with open(path, "w", encoding="utf-8") as f:
        for idx, ts, text in entries:
            f.write(f"{idx}\n{ts}\n{text}\n\n")

# -------------------- 对齐切分 --------------------

def flatten_for_align(text: str) -> str:
    return text.replace("\r", "").replace("\n", "")

def segment_corrected_by_recognized_boundaries(recognized_full: str,
                                               corrected_full: str,
                                               line_lengths: list[int]):
    boundaries = [0]
    acc = 0
    for L in line_lengths:
        acc += L
        boundaries.append(acc)

    sm = difflib.SequenceMatcher(None, recognized_full, corrected_full, autojunk=False)
    ops = sm.get_opcodes()

    out_lines, buf = [], []
    r_pos, next_bi = 0, 1
    next_boundary = boundaries[next_bi] if next_bi < len(boundaries) else len(recognized_full)

    def flush_line():
        nonlocal buf, out_lines, next_bi, next_boundary
        out_lines.append("".join(buf))
        buf = []
        next_bi += 1
        next_boundary = boundaries[next_bi] if next_bi < len(boundaries) else boundaries[-1]

    for tag, i1, i2, j1, j2 in ops:
        if tag in ("equal", "replace"):
            while r_pos < i2:
                take = min(i2 - r_pos, next_boundary - r_pos)
                recog_len_total = i2 - i1
                corr_len_total  = j2 - j1
                start_ratio = (r_pos - i1) / max(1, recog_len_total)
                end_ratio   = (r_pos + take - i1) / max(1, recog_len_total)
                cj_start = j1 + round(start_ratio * corr_len_total)
                cj_end   = j1 + round(end_ratio   * corr_len_total)
                if cj_start < cj_end:
                    buf.append(corrected_full[cj_start:cj_end])
                r_pos += take
                if r_pos == next_boundary:
                    flush_line()

        elif tag == "delete":
            while r_pos < i2:
                take = min(i2 - r_pos, next_boundary - r_pos)
                r_pos += take
                if r_pos == next_boundary:
                    flush_line()

        elif tag == "insert":
            buf.append(corrected_full[j1:j2])

    if buf:
        while len(out_lines) < len(line_lengths) - 1:
            out_lines.append("")
        out_lines.append("".join(buf))

    if len(out_lines) < len(line_lengths):
        out_lines += [""] * (len(line_lengths) - len(out_lines))
    elif len(out_lines) > len(line_lengths):
        extra = "".join(out_lines[len(line_lengths)-1:])
        out_lines = out_lines[:len(line_lengths)-1] + [extra]

    cleaned = []
    for line in out_lines:
        # line = re.sub(r"\s+", "", line)
        # line = re.sub(r'^(…{1,2}|\.{3,}|[，。！？；：、”])+', '', line)
        # line = re.sub(r'(…{1,2}|\.{3,}|[，。！？；：、“])+$', '', line)
        # 同时匹配中英文符号
        line = re.sub(r"\s+", "", line)
        line = re.sub(r'^(…{1,2}|\.{3,}|[，,。.!！？?；;：:、”“"“])+', '', line)
        line = re.sub(r'(…{1,2}|\.{3,}|[，,。.!！？?；;：:、”“"“])+$', '', line)

        cleaned.append(line)

    return cleaned

# -------------------- 外部调用 --------------------

def correct_srt_file(original_text: str, srt_path: str,
                     overwrite: bool = True, backup: bool = False,
                     out_path: str = None):
    """
    original_text: 原始完整文本（直接传字符串）
    srt_path: 输入字幕文件路径
    overwrite: 是否覆盖原文件（默认 True）
    backup: 覆盖时是否先生成 .bak 文件（默认 True）
    out_path: 如果不覆盖，可以指定输出文件路径
    """
    original_full = original_text.replace("\r", "").replace("\n", "").strip()
    entries = read_srt(srt_path)

    recognized_lines = [flatten_for_align(txt) for _, _, txt in entries]
    recognized_full = "".join(recognized_lines)

    corrected_full = correct_text_with_pinyin(original_full, recognized_full)

    line_lengths = [len(s) for s in recognized_lines]
    corrected_lines = segment_corrected_by_recognized_boundaries(
        recognized_full, corrected_full, line_lengths
    )

    corrected_entries = []
    for (idx, ts, _), line_text in zip(entries, corrected_lines):
        corrected_entries.append((idx, ts, line_text))

    # 目标路径
    if overwrite:
        if backup:
            shutil.copy(srt_path, srt_path + ".bak")
            logging.info("已生成备份文件：%s.bak", srt_path)
        target_path = srt_path
    else:
        target_path = out_path or (srt_path + ".corrected.srt")

    write_srt(target_path, corrected_entries)
    logging.info("已生成 %s （逐行对齐修正完成）", target_path)

if __name__ == '__main__':
    generate_subtitle("C:\\Users\\lxc18\\SonicVale\\1\\1\\audio\\id_2.wav","C:\\Users\\lxc18\\SonicVale\\1\\1\\audio\\id_1.srt")


# -------------------- LLM 字幕矫正 --------------------

def correct_srt_file_with_llm(
    original_text: str,
    srt_path: str,
    llm_engine: LLMEngine,
    batch_size: int = 20,
    overwrite: bool = True,
    backup: bool = False,
    out_path: str = None
):
    """
    使用LLM进行字幕矫正，分批处理
    
    original_text: 原始完整文本
    srt_path: 输入字幕文件路径
    llm_engine: LLM引擎实例
    batch_size: 每批处理的字幕条数（默认20条）
    overwrite: 是否覆盖原文件
    backup: 覆盖时是否生成.bak文件
    out_path: 如果不覆盖，可以指定输出文件路径
    """
    original_full = original_text.replace("\r", "").replace("\n", "").strip()
    entries = read_srt(srt_path)
    
    if not entries:
        logging.warning("字幕文件为空：%s", srt_path)
        return
    
    # 分批处理
    corrected_entries = []
    total_batches = (len(entries) + batch_size - 1) // batch_size
    
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(entries))
        batch_entries = entries[start_idx:end_idx]
        
        logging.info("处理字幕批次 %d/%d (第%d-%d条)", 
                     batch_idx + 1, total_batches, start_idx + 1, end_idx)
        
        # 准备当前批次的字幕数据
        subtitle_lines = [
            {"index": idx, "text": txt.replace("\n", " ").replace('"', '\\"')}
            for idx, ts, txt in batch_entries
        ]
        
        # 调用LLM进行矫正
        prompt = get_subtitle_correction_prompt(original_full, subtitle_lines)
        
        try:
            response = llm_engine.generate_text(prompt)
            corrected_batch = llm_engine.save_load_json(response)
            
            # 构建索引映射
            corrected_map = {item["index"]: item["corrected_text"] for item in corrected_batch}
            
            # 处理当前批次的结果
            for idx, ts, original_txt in batch_entries:
                corrected_text = corrected_map.get(idx, original_txt)
                # 清理文本
                corrected_text = clean_subtitle_text(corrected_text)
                corrected_entries.append((idx, ts, corrected_text))
                
        except Exception as e:
            logging.error("批次 %d 矫正失败，使用原始文本: %s", batch_idx + 1, str(e))
            # 失败时保留原始文本
            for idx, ts, txt in batch_entries:
                corrected_entries.append((idx, ts, txt))
    
    # 确定目标路径
    if overwrite:
        if backup:
            shutil.copy(srt_path, srt_path + ".bak")
            logging.info("已生成备份文件：%s.bak", srt_path)
        target_path = srt_path
    else:
        target_path = out_path or (srt_path + ".corrected.srt")
    
    write_srt(target_path, corrected_entries)
    logging.info("已生成 %s （LLM字幕矫正完成）", target_path)


def clean_subtitle_text(text: str) -> str:
    """清理字幕文本"""
    # 去除空白字符
    text = re.sub(r"\s+", "", text)
    # 清理首尾标点
    text = re.sub(r'^(…{1,2}|\.{3,}|[，,。.!！？?;；:：、"“”""])+', '', text)
    text = re.sub(r'(…{1,2}|\.{3,}|[，,。.!！？?;；:：、"“”""])+$', '', text)
    return text
