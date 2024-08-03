import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel, QRadioButton, QButtonGroup, QPushButton, QComboBox
import openai
from PIL import Image
import io
import moviepy.editor as mp
import os
import pyaudio
import wave
import time

# 設定 API 金鑰
def read_api_key(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        print("Reading API Key from", filepath, "---- Start")
        api_key = file.readline().split('=')[1].strip().strip("'")
        print("Reading API Key from", filepath, "---- Done")
    return api_key

def create_client(api_key):
    openai.api_key = api_key
    return openai

# PyQt 主窗口
class OpenAIInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenAI Chat Interface")
        self.setGeometry(100, 100, 800, 600)

        # 主窗口布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 模型選擇部分
        self.model_selection_label = QLabel("選擇模型:")
        self.layout.addWidget(self.model_selection_label)

        self.model_selection = QComboBox()
        self.model_selection.addItems(["GPT-4o", "GPT-4o mini", "Whisper", "TTS", "DALL·E"])
        self.model_selection.setCurrentText("GPT-4o mini")
        self.layout.addWidget(self.model_selection)

        # 輸入部分布局
        self.input_layout = QVBoxLayout()

        # 選擇輸入類型
        self.input_type_label = QLabel("選擇輸入類型:")
        self.input_layout.addWidget(self.input_type_label)

        self.input_type_group = QButtonGroup(self)
        self.input_type_buttons = []

        for input_type in ["文字", "影像", "語音", "影片"]:
            button = QRadioButton(input_type)
            self.input_layout.addWidget(button)
            self.input_type_group.addButton(button)
            self.input_type_buttons.append(button)

        self.input_type_buttons[0].setChecked(True)

        # 輸入框
        self.input_text = QTextEdit()
        self.input_layout.addWidget(self.input_text)

        self.layout.addLayout(self.input_layout)

        # 發送按鈕
        self.send_button = QPushButton("發送")
        self.send_button.setFixedSize(100, 40)  # 設置按鈕大小
        self.send_button.clicked.connect(self.send_to_openai)
        self.layout.addWidget(self.send_button)

        # 輸出部分布局
        self.output_layout = QVBoxLayout()

        # 選擇輸出類型
        self.output_type_label = QLabel("選擇輸出類型:")
        self.output_layout.addWidget(self.output_type_label)

        self.output_type_group = QButtonGroup(self)
        self.output_type_buttons = []

        for output_type in ["文字", "影像"]:
            button = QRadioButton(output_type)
            self.output_layout.addWidget(button)
            self.output_type_group.addButton(button)
            self.output_type_buttons.append(button)

        self.output_type_buttons[0].setChecked(True)

        # 顯示框
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_layout.addWidget(self.output_text)

        self.layout.addLayout(self.output_layout)

    def send_to_openai(self):
        input_content = self.input_text.toPlainText().strip()
        if not input_content:
            self.output_text.setPlainText("請輸入文字內容。")
            return

        selected_input_button = self.input_type_group.checkedButton()
        data_type = selected_input_button.text()

        selected_model = self.model_selection.currentText()
        model_mapping = {
            "GPT-4o": "gpt-4o",
            "GPT-4o mini": "gpt-4o-mini",
            "Whisper": "whisper-1",
            "TTS": "tts-1",
            "DALL·E": "dall-e-3"
        }
        model = model_mapping.get(selected_model, "gpt-4o-mini")

        try:
            if data_type == "文字":
                responses = make_text_requests(client, model, [input_content])
            elif data_type == "語音":
                audio_file = record_audio()
                if audio_file:
                    responses = make_audio_requests(client, model, [{'audio': audio_file, 'description': input_content}])
                else:
                    responses = ["錄音失敗。"]
            else:
                responses = ["暫時不支援此類型的處理。"]

            self.output_text.setPlainText("\n".join(responses))
        except Exception as e:
            self.output_text.setPlainText(f"發生錯誤: {str(e)}")
            print(f"發生錯誤: {str(e)}")

# 其他函數
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
        message_content = response.choices[0].message.content
        print(f"=== Response #{index} ===")  # 顯示回應的次序
        print("Response from the OpenAI API:", message_content)
        responses.append(message_content)
    print("Making text requests to the OpenAI API ---- Done")
    return responses

def make_audio_requests(client, model, inputs):
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
            message_content = str(response)  # 如果無法提取文字，則打印原始 response
        print("Response from the OpenAI API:", message_content)
        responses.append(message_content)
    print("Making audio requests to the OpenAI API ---- Done")
    return responses

def record_audio(filename="temp_audio.wav"):
    chunk = 1024
    sample_format = pyaudio.paInt16
    channels = 1
    fs = 44100
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
if __name__ == "__main__":
    api_key = read_api_key('key.txt')
    client = create_client(api_key)
    app = QApplication(sys.argv)
    mainWindow = OpenAIInterface()
    mainWindow.show()
    sys.exit(app.exec())
