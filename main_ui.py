import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel, QRadioButton, QButtonGroup, QPushButton, QComboBox, QFileDialog, QDialog
from PyQt6.QtGui import QPixmap  # QPixmap 應從 PyQt6.QtGui 模組中導入
import openai
from PIL import Image
import io
import moviepy.editor as mp
import os
import pyaudio
import wave
import time
import requests
from PyQt6.QtGui import QPixmap

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
            button.toggled.connect(self.on_input_type_changed)
            self.input_layout.addWidget(button)
            self.input_type_group.addButton(button)
            self.input_type_buttons.append(button)

        self.input_type_buttons[0].setChecked(True)

        # 初始化所有控件
        self.input_text = QTextEdit()
        self.input_layout.addWidget(self.input_text)

        # 控件初始化部分
        self.image_browse_button = QPushButton("瀏覽圖片")
        self.image_browse_button.clicked.connect(self.browse_image)
        self.input_layout.addWidget(self.image_browse_button)
        self.image_browse_button.hide()

        self.audio_file_button = QRadioButton("選擇語音檔案")
        self.audio_record_button = QRadioButton("直接錄音")
        self.audio_buttons_group = QButtonGroup(self)
        self.audio_buttons_group.addButton(self.audio_file_button)
        self.audio_buttons_group.addButton(self.audio_record_button)
        self.audio_file_button.setChecked(True)
        self.input_layout.addWidget(self.audio_file_button)
        self.input_layout.addWidget(self.audio_record_button)
        self.audio_file_button.hide()
        self.audio_record_button.hide()

        self.audio_browse_button = QPushButton("瀏覽語音檔案")
        self.audio_browse_button.clicked.connect(self.browse_audio)
        self.input_layout.addWidget(self.audio_browse_button)
        self.audio_browse_button.hide()

        self.video_browse_button = QPushButton("瀏覽影片")
        self.video_browse_button.clicked.connect(self.browse_video)
        self.input_layout.addWidget(self.video_browse_button)
        self.video_browse_button.hide()

        self.layout.addLayout(self.input_layout)

        self.send_button = QPushButton("發送")
        self.send_button.setFixedSize(150, 40)
        self.send_button.clicked.connect(self.send_to_openai)
        self.layout.addWidget(self.send_button)

        self.output_layout = QVBoxLayout()

        self.output_type_label = QLabel("選擇輸出類型:")
        self.output_layout.addWidget(self.output_type_label)

        self.output_type_group = QButtonGroup(self)
        self.output_type_buttons = []

        for output_type in ["文字", "影像", "語音"]:
            button = QRadioButton(output_type)
            button.toggled.connect(self.on_output_type_changed)
            self.output_layout.addWidget(button)
            self.output_type_group.addButton(button)
            self.output_type_buttons.append(button)

        self.output_type_buttons[0].setChecked(True)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_layout.addWidget(self.output_text)

        self.output_image_label = QLabel()  # 用於顯示生成的圖片
        self.output_layout.addWidget(self.output_image_label)
        self.output_image_label.hide()

        self.layout.addLayout(self.output_layout)

        self.selected_image_path = None
        self.selected_audio_path = None
        self.selected_video_path = None

        # 在所有組件初始化完成後調用此方法
        self.on_input_type_changed()

    def on_input_type_changed(self):
        selected_button = self.input_type_group.checkedButton()
        
        # 確保屬性存在再操作
        if hasattr(self, 'image_browse_button'):
            self.image_browse_button.hide()
        
        if hasattr(self, 'audio_file_button'):
            self.audio_file_button.hide()
        
        if hasattr(self, 'audio_record_button'):
            self.audio_record_button.hide()
        
        if hasattr(self, 'audio_browse_button'):
            self.audio_browse_button.hide()
        
        if hasattr(self, 'video_browse_button'):
            self.video_browse_button.hide()
        
        if selected_button.text() == "影像":
            if hasattr(self, 'image_browse_button'):
                self.image_browse_button.show()
            self.model_selection.clear()
            self.model_selection.addItems(["DALL·E"])
        elif selected_button.text() == "語音":
            if hasattr(self, 'audio_file_button'):
                self.audio_file_button.show()
            if hasattr(self, 'audio_record_button'):
                self.audio_record_button.show()
            if hasattr(self, 'audio_browse_button'):
                self.audio_browse_button.show()
            self.model_selection.clear()
            self.model_selection.addItems(["Whisper"])
        elif selected_button.text() == "影片":
            if hasattr(self, 'video_browse_button'):
                self.video_browse_button.show()
            self.model_selection.clear()
            self.model_selection.addItems([])  # 暫無影片相關模型
        else:  # 文字
            if hasattr(self, 'output_type_group'):
                self.on_output_type_changed()

    def on_output_type_changed(self):
        selected_input_button = self.input_type_group.checkedButton()
        selected_output_button = self.output_type_group.checkedButton()

        if selected_input_button.text() == "文字":
            if selected_output_button and selected_output_button.text() == "文字":
                self.model_selection.clear()
                self.model_selection.addItems(["GPT-4o", "GPT-4o mini"])
            elif selected_output_button and selected_output_button.text() == "影像":
                self.model_selection.clear()
                self.model_selection.addItems(["DALL·E"])
            elif selected_output_button and selected_output_button.text() == "語音":
                self.model_selection.clear()
                self.model_selection.addItems(["TTS"])
            else:
                self.model_selection.clear()
        elif selected_input_button.text() == "語音" and selected_output_button.text() == "文字":
            self.model_selection.clear()
            self.model_selection.addItems(["Whisper"])
        else:
            self.model_selection.clear()  # 非文字輸入不處理輸出類型變化

    def browse_image(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.bmp)")
        if file_dialog.exec():
            self.selected_image_path = file_dialog.selectedFiles()[0]
            self.output_text.setPlainText(f"已選擇圖片: {self.selected_image_path}")

    def browse_audio(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio Files (*.wav *.mp3)")
        if file_dialog.exec():
            self.selected_audio_path = file_dialog.selectedFiles()[0]
            self.output_text.setPlainText(f"已選擇語音檔案: {self.selected_audio_path}")

    def browse_video(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Video Files (*.mp4 *.avi *.mov)")
        if file_dialog.exec():
            self.selected_video_path = file_dialog.selectedFiles()[0]
            self.output_text.setPlainText(f"已選擇影片: {self.selected_video_path}")

    def display_image_from_url(self, url):
        try:
            response = requests.get(url)
            image = Image.open(io.BytesIO(response.content))
            
            # 保存原始圖片以便在放大時使用
            image.save("/tmp/full_size_image.png")

            # 縮放圖片為縮略圖尺寸
            thumbnail_size = (200, 200)
            image.thumbnail(thumbnail_size)
            thumbnail_path = "/tmp/thumbnail_image.png"
            image.save(thumbnail_path)

            # 顯示縮略圖
            pixmap = QPixmap(thumbnail_path)
            self.output_image_label.setPixmap(pixmap)
            self.output_image_label.setFixedSize(pixmap.size())
            self.output_image_label.show()
            self.output_text.hide()

            # 點擊圖片放大顯示
            self.output_image_label.mousePressEvent = self.show_full_size_image

        except Exception as e:
            self.output_text.setPlainText(f"無法顯示圖片: {str(e)}")
            print(f"無法顯示圖片: {str(e)}")

    def show_full_size_image(self, event):
        dialog = QDialog(self)
        dialog.setWindowTitle("Full Size Image")

        layout = QVBoxLayout(dialog)
        full_image_label = QLabel(dialog)

        full_image_pixmap = QPixmap("/tmp/full_size_image.png")
        full_image_label.setPixmap(full_image_pixmap)

        layout.addWidget(full_image_label)
        dialog.setLayout(layout)
        dialog.exec()

    def send_to_openai(self):
        selected_model = self.model_selection.currentText()
        model_mapping = {
            "GPT-4o": "gpt-4o-2024-08-06",
            "GPT-4o mini": "gpt-4o-mini",
            "Whisper": "whisper-1",
            "TTS": "tts-1",
            "DALL·E": "dall-e-3"
        }
        model = model_mapping.get(selected_model, "gpt-4o-mini")

        selected_input_button = self.input_type_group.checkedButton()
        input_data_type = selected_input_button.text()

        selected_output_button = self.output_type_group.checkedButton()
        output_data_type = selected_output_button.text()

        self.output_text.setPlainText("按下發送")
        self.output_image_label.hide()  # 隱藏圖片顯示區域
        self.output_text.show()  # 顯示文字輸出區域

        try:
            if input_data_type == "文字" and output_data_type == "文字":
                input_content = self.input_text.toPlainText().strip()
                if not input_content:
                    self.output_text.setPlainText("請輸入文字內容。")
                    return
                responses = make_text_requests(client, model, [input_content])
            elif input_data_type == "文字" and output_data_type == "語音":
                input_content = self.input_text.toPlainText().strip()
                if not input_content:
                    self.output_text.setPlainText("請輸入文字內容。")
                    return
                responses = make_audio_requests(client, model, [{'text': input_content}])
            ##Response
            #ImagesResponse(created=1725159299, data=[Image(b64_json=None, 
            #revised_prompt='
            # Generate an image depicting the solar system, 
            # showing the eight planets - Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune - orbiting the sun. 
            # The planets should be in order of distance from the sun, with the innermost planet, Mercury, 
            # closest to the sun, and the outermost planet, Neptune, the farthest away. Accurately depict their respective sizes and colors, 
            # such as the blue-green hue of Earth, the reddish appearance of Mars, and the iconic rings of Saturn. 
            # Furthermore, include the asteroid belt between Mars and Jupiter and the icy Kuiper belt beyond Neptune. 
            # Use a perspective where all the planets can be seen clearly.', 
            # url='https://oaidalleapiprodscus.blob.core.windows.net/private/org-QEdftdO08A3kXpGWXZdijTzU/user-yvctgJSLGyQpT5InKqQ995iy/img-a5nP7m7SCRzV7AwXmQb6AFT6.png?st=2024-09-01T01%3A54%3A59Z&se=2024-09-01T03%3A54%3A59Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=d505667d-d6c1-4a0a-bac7-5c84a87759f8&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-08-31T23%3A38%3A35Z&ske=2024-09-01T23%3A38%3A35Z&sks=b&skv=2024-08-04&sig=ytXYyVrMi5jWrT24gq2Crs%2BQ5ulLtV15NG7EXkNuO0Y%3D')])
            ##
            elif input_data_type == "文字" and output_data_type == "影像":
                input_content = self.input_text.toPlainText().strip()
                if not input_content:
                    self.output_text.setPlainText("請輸入文字內容。")
                    return
                responses = make_image_requests(client, model, [{'text': input_content}])
                # 顯示影像結果
                for response in responses:
                    self.display_image_from_url(response)
            elif input_data_type == "語音" and output_data_type == "文字":
                if self.audio_file_button.isChecked():
                    if self.selected_audio_path:
                        audio_data = read_audio(self.selected_audio_path)
                        responses = make_audio_requests(client, model, [{'audio': audio_data, 'description': self.input_text.toPlainText().strip()}])
                    else:
                        self.output_text.setPlainText("請選擇一個語音檔案。")
                        return
                elif self.audio_record_button.isChecked():
                    self.output_text.setPlainText("正在錄音...")
                    audio_file = record_audio()
                    if audio_file:
                        self.output_text.setPlainText("錄音完成，發送中...")
                        responses = make_audio_requests(client, model, [{'audio': audio_file, 'description': self.input_text.toPlainText().strip()}])
                    else:
                        responses = ["錄音失敗。"]
            elif input_data_type == "影像" and output_data_type == "文字":
                if self.selected_image_path:
                    image_data = read_image(self.selected_image_path)
                    responses = make_text_requests(client, model, [image_data])
                else:
                    self.output_text.setPlainText("請選擇一個圖片檔案。")
                    return
            else:
                responses = ["暫時不支援此類型的處理。"]

            self.output_text.setPlainText("\n".join(responses))
        except Exception as e:
            self.output_text.setPlainText(f"發生錯誤: {str(e)}")
            print(f"發生錯誤: {str(e)}")

# 其他函數
def read_text(filepath):
    if not os.path.exists(filepath):
        print(f"Text file {filepath} does not exist。")
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
        if 'audio' in input_data:
            response = client.audio.transcriptions.create(
                model=model, 
                file=input_data['audio'], 
                response_format="text",
                prompt=input_data['description']
            )
        else:
            response = client.audio.transcriptions.create(
                model=model,
                file=io.BytesIO(input_data['text'].encode('utf-8')),
                response_format="text"
            )
        print(f"=== Response #{index} ===")
        try:
            message_content = response['text']
        except (TypeError, KeyError) as e:
            print(f"Error extracting text from response: {e}")
            message_content = str(response)
        print("Response from the OpenAI API:", message_content)
        responses.append(message_content)
    print("Making audio requests to the OpenAI API ---- Done")
    return responses

def make_image_requests(client, model, inputs):
    print("Making image requests to the OpenAI API ---- Start")
    responses = []
    for index, input_data in enumerate(inputs, start=1):
        response = client.images.generate(
            model=model,
            prompt=input_data['text']
        )
        print(f"=== Response #{index} ===")
        try:
            image_url = response.data[0].url
            print("Image URL:", image_url)
            responses.append(image_url)
        except (TypeError, KeyError) as e:
            print(f"Error extracting image URL from response: {e}")
            message_content = str(response)
            responses.append(message_content)
    print("Making image requests to the OpenAI API ---- Done")
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
