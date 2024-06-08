from PIL import Image, ImageDraw

# 生成 input_image.png 文件
image = Image.new('RGB', (100, 100), color = (73, 109, 137))
draw = ImageDraw.Draw(image)
draw.text((10, 40), "示例圖像", fill=(255, 255, 0))
image.save('input_image.png')
