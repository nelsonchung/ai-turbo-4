from pydub import AudioSegment
from pydub.generators import Sine

# 生成 input_audio.mp3 文件
tone = Sine(440).to_audio_segment(duration=1000)  # 1 秒鐘的 A4 音
tone.export('input_audio.mp3', format='mp3')
