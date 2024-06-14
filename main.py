import openai
from PIL import Image
import io
import moviepy.editor as mp
import os
import pyaudio
import wave
import time

def read_api_key(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        print("Reading API Key from", filepath, "---- Start")
        api_key = file.readline().split('=')[1].strip().strip("'")
        print("Reading API Key from", filepath, "---- Done")
    return api_key

def create_client(api_key):
    openai.api_key = api_key
    return openai

def read_text(filepath):
    if not os.path.exists(filepath):
        print(f"Text file {filepath} does not exist.")
        return None
    with open(filepath, 'r', encoding='utf-8') as file:
        print("Reading the", filepath, "file ---- Start")
        input_content = file.read()
        print("Reading the", filepath, "file ---- End")
    return input_content

def read_image(filepath):
    if not os.path.exists(filepath):
        print(f"Image file {filepath} does not exist。")
        return None
    print("Reading image file", filepath, "---- Start")
    with open(filepath, 'rb') as file:
        image = Image.open(file)
        byte_arr = io.BytesIO()
        image.save(byte_arr, format=image.format)
        byte_data = byte_arr.getvalue()
    print("Reading image file", filepath, "---- Done")
    return byte_data

def read_audio(filepath):
    if not os.path.exists(filepath):
        print(f"Audio file {filepath} does not exist。")
        return None
    print("Reading audio file", filepath, "---- Start")
    audio_file = open(filepath, "rb")
    print("Reading audio file", filepath, "---- Done")
    return audio_file

def read_video(filepath):
    if not os.path.exists(filepath):
        print(f"Video file {filepath} does not exist。")
        return None
    print("Reading video file", filepath, "---- Start")
    video = mp.VideoFileClip(filepath)
    video.write_videofile("temp_video.mp4", codec="libx264")
    with open("temp_video.mp4", "rb") as file:
        byte_data = file.read()
    os.remove("temp_video.mp4")
    print("Reading video file", filepath, "---- Done")
    return byte_data

def split_input(input_content, max_tokens):
    if input_content is None:
        return []
    tokens = input_content.split()
    chunks = []
    current_chunk = []

    for token in tokens:
        current_chunk.append(token)
        if len(' '.join(current_chunk)) > max_tokens:
            chunks.append(' '.join(current_chunk[:-1]))
            current_chunk = [token]
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def make_text_requests(client, model, inputs):
    print("Making text requests to the OpenAI API ---- Start")
    responses = []
    for index, input_data in enumerate(inputs, start=1):
        messages = [{"role": "system", "content": "你是一位程式規劃與寫作專家，請協助讀懂我的程式碼並記憶起來。後續會提供你需要完成的需求。請使用繁體中文回答我。"},
                    {"role": "user", "content": input_data}]
        response = client.chat.completions.create(model=model, messages=messages)
        #message_content = response['choices'][0]['message']['content']
        message_content = response.choices[0].message.content
        print(f"=== Response #{index} ===")  # 顯示回應的次序
        print("Response from the OpenAI API:", message_content)
        responses.append(message_content)
    print("Making text requests to the OpenAI API ---- Done")
    return responses

def make_audio_requests(client, model, inputs):
    # Reference: https://platform.openai.com/docs/guides/speech-to-text
    print("Making audio requests to the OpenAI API ---- Start")
    responses = []
    for index, input_data in enumerate(inputs, start=1):
        response = client.audio.transcriptions.create(
            model=model, 
            file=input_data['audio'], 
            response_format="text",
            prompt=input_data['description']
        )
        print(f"=== Response #{index} ===")  # 顯示回應的次序
        print("Response object:", response)  # 調試打印 response 對象
        try:
            message_content = response['text']
        except (TypeError, KeyError) as e:
            print(f"Error extracting text from response: {e}")
            message_content = str(response)  # 如果無法提取文本，則打印原始 response
        print("Response from the OpenAI API:", message_content)
        responses.append(message_content)
    print("Making audio requests to the OpenAI API ---- Done")
    return responses

def make_requests(client, model, inputs, data_type):
    if data_type == 'text':
        return make_text_requests(client, model, inputs)
    elif data_type == 'audio':
        return make_audio_requests(client, model, inputs)
    else:
        print("Unsupported data type.")
        return []

def get_user_choices():
    choices = {'text': False, 'image': False, 'audio': False, 'video': False}
    print("請選擇輸入的數據類型（可多選，輸入完成後按Enter）:")
    print("1. 文字")
    print("2. 圖片")
    print("3. 聲音")
    print("4. 影片")
    selected_options = input("請輸入選項號碼（用空格分隔，例如：1 2 3）: ").split()
    
    for option in selected_options:
        if option == '1':
            choices['text'] = True
        elif option == '2':
            choices['image'] = True
        elif option == '3':
            choices['audio'] = True
        elif option == '4':
            choices['video'] = True
        else:
            print(f"無效的選項：{option}")
    
    return choices

def get_user_question():
    question = input("請輸入你要詢問的問題內容: ")
    return question

def get_user_description(data_type):
    description = input(f"請輸入關於 {data_type} 的說明文字: ")
    return description

def get_audio_choice():
    print("請選擇音頻輸入方式：")
    print("1. 使用預設音頻")
    print("2. 現在錄音")
    choice = input("請輸入選項號碼（1或2）: ")
    return choice

def record_audio(filename="temp_audio.wav"):
    # 初始參數設定
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 1
    fs = 44100  # Record at 44100 samples per second
    duration = 5

    print("倒數計時開始錄音：")
    for i in range(3, 0, -1):
        print(i)
        time.sleep(1)
    print("開始錄音...")
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=sample_format, channels=1, rate=fs, input=True, frames_per_buffer=chunk)
        frames = []

        for _ in range(0, int(fs / chunk * duration)):
            data = stream.read(chunk)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(fs)
        wf.writeframes(b''.join(frames))
        wf.close()

        print("錄音完成，儲存為", filename)
        return read_audio(filename)
    except Exception as e:
        print(f"錄音過程中發生錯誤: {e}")
        return None

# 主程序
api_key = read_api_key('key.txt')
client = create_client(api_key)

# 暫時隱藏的預設文本輸入功能
# text_content = read_text('generate_utility/input.txt')
image_data = read_image('generate_utility/input_image.png')  # 假設存在 image 文件
audio_data = read_audio('nelson_input_audio.mp3')  # 假設存在 audio 文件
video_data = read_video('generate_utility/input_video.mp4')  # 假設存在 video 文件

max_tokens = 10000  # 將最大令牌數作為可調參數

# text_chunks = split_input(text_content, max_tokens)  # 分割文本塊

# 根據用戶選擇設置輸入數據組合
choices = get_user_choices()
inputs = []

data_type = None
if choices['text']:
    data_type = 'text'
    question = get_user_question()
    inputs.append(question)
if choices['image'] and image_data:
    data_type = 'image'
    description = get_user_description('image')
    inputs.append({'image': image_data, 'description': description})
if choices['audio']:
    audio_choice = get_audio_choice()
    if audio_choice == '1':
        if audio_data:
            data_type = 'audio'
            description = get_user_description('audio')
            inputs.append({'audio': audio_data, 'description': description})
        else:
            print("預設音頻文件不存在。")
    elif audio_choice == '2':
        recorded_audio = record_audio()
        if recorded_audio:
            data_type = 'audio'
            description = get_user_description('audio')
            inputs.append({'audio': recorded_audio, 'description': description})
        else:
            print("錄音失敗。")
if choices['video'] and video_data:
    data_type = 'video'
    description = get_user_description('video')
    inputs.append({'video': video_data, 'description': description})

if not inputs:
    print("未選擇任何有效的數據類型，請重新運行程序並選擇至少一個數據類型。")
    exit()

if data_type == 'text':
    responses = make_requests(client, "gpt-4o", inputs, data_type)
elif data_type == 'audio':
    responses = make_requests(client, "whisper-1", inputs, data_type)
else:
    responses = make_requests(client, "gpt-4o", inputs, data_type)  # 默認使用 gpt-4o 處理圖像和視頻

for response in responses:
    print(response)
