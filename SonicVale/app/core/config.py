import os

import os, sys
from pathlib import Path
# 得到默认配置文件
def getConfigPath():
    # 用户 目录下SonicVale目录
    user_dir = os.path.join(os.path.expanduser("~"), "SonicVale")

    # 如果目录不存在，创建它
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)

    # 返回 config.json 路径（目录已保证存在）
    return user_dir

def getFfmpegPath():
    BASE_DIR = getattr(sys, "_MEIPASS", Path(os.path.abspath(".")))
    FFMPEG_PATH = os.path.join(BASE_DIR, "core", "ffmpeg", "ffmpeg.exe")
    return FFMPEG_PATH