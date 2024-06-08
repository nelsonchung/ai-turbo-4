from moviepy.editor import TextClip, concatenate_videoclips

# 生成 input_video.mp4 文件
clip = TextClip("示例視頻", fontsize=70, color='white', size=(640, 480))
clip = clip.set_duration(5)  # 5 秒鐘的視頻
clip.write_videofile('input_video.mp4', fps=24)
