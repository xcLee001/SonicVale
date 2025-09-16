from app.core.subtitle.BcutASR import BcutASR


def generate_subtitle(audio_file,save_path):
    asr = BcutASR(audio_file)
    result = asr.run()
    result.to_srt(save_path)
    return result


if __name__ == '__main__':
    generate_subtitle("C:\\Users\\lxc18\\SonicVale\\1\\1\\audio\\id_2.wav","C:\\Users\\lxc18\\SonicVale\\1\\1\\audio\\id_1.srt")