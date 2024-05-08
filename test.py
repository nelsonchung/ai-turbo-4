from openai import OpenAI

def read_api_key(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        print("Reading API Key from", filepath, "---- Start")
        api_key = file.readline().split('=')[1].strip().strip("'")
        print("Reading API Key from", filepath, "---- Done")
    return api_key

def create_client(api_key):
    return OpenAI(api_key=api_key)

def read_input(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        print("Reading the", filepath, "file ---- Start")
        input_content = file.read()
        print("Reading the", filepath, "file ---- End")
    return input_content

def split_input(input_content, max_tokens):
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

def make_requests(client, model, chunks):
    print("Making requests to the OpenAI API ---- Start")
    responses = []
    for index, chunk in enumerate(chunks, start=1):  # 使用 enumerate 獲取索引，從 1 開始
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位程式規劃與寫作專家，請協助讀懂我的程式碼並記憶起來。後續會提供你需要完成的需求。請使用繁體中文回答我。"},
                {"role": "user", "content": chunk}
            ]
        )
        # 更新此行以適應對象訪問方式
        message_content = response.choices[0].message.content
        print(f"=== Response #{index} ===")  # 顯示回應的次序
        print("Response from the OpenAI API:", message_content)
        responses.append(message_content)
    print("Making requests to the OpenAI API ---- Done")
    return responses

# 主程序
api_key = read_api_key('key.txt')
client = create_client(api_key)
input_content = read_input('input.txt')
max_tokens = 10000  # 將最大令牌數作為可調參數

chunks = split_input(input_content, max_tokens)
responses = make_requests(client, "gpt-4", chunks)  # 根據您的實際模型名稱調整

for response in responses:
    print(response)
