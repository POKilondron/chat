
from PIL import Image, ImageDraw
import math
import os

def create_icon():
    # Размер изображения
    size = (256, 256)
    # Создаем новое изображение с белым фоном
    image = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Центр изображения
    center_x, center_y = size[0] // 2, size[1] // 2
    radius = min(size) // 3
    
    # Рисуем треугольники
    # Красный треугольник
    red_points = [
        (center_x - radius * math.cos(math.radians(30)), center_y - radius * math.sin(math.radians(30))),
        (center_x - radius * math.cos(math.radians(150)), center_y - radius * math.sin(math.radians(150))),
        (center_x - radius * math.cos(math.radians(270)), center_y - radius * math.sin(math.radians(270)))
    ]
    draw.polygon(red_points, fill=(255, 0, 0, 200))
    
    # Желтый треугольник
    yellow_points = [
        (center_x + radius * math.cos(math.radians(30)), center_y - radius * math.sin(math.radians(30))),
        (center_x + radius * math.cos(math.radians(150)), center_y - radius * math.sin(math.radians(150))),
        (center_x + radius * math.cos(math.radians(270)), center_y - radius * math.sin(math.radians(270)))
    ]
    draw.polygon(yellow_points, fill=(255, 255, 0, 200))
    
    # Зеленый треугольник
    green_points = [
        (center_x, center_y - radius),
        (center_x - radius * math.cos(math.radians(30)), center_y + radius * math.sin(math.radians(30))),
        (center_x + radius * math.cos(math.radians(30)), center_y + radius * math.sin(math.radians(30)))
    ]
    draw.polygon(green_points, fill=(0, 255, 0, 200))
    
    # Синий круг по центру
    circle_radius = radius // 2
    draw.ellipse(
        (center_x - circle_radius, center_y - circle_radius, 
         center_x + circle_radius, center_y + circle_radius), 
        fill=(0, 0, 255, 200)
    )
    
    # Сохраняем изображение
    image.save('generated-icon.png')
    
    # Конвертируем в .ico для Windows
    try:
        icon_img = Image.open('generated-icon.png')
        if not os.path.exists('static'):
            os.makedirs('static')
        icon_img.save('static/favicon.ico', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        print("Иконка успешно создана!")
    except Exception as e:
        print(f"Ошибка при создании иконки: {e}")

if __name__ == "__main__":
    create_icon()
