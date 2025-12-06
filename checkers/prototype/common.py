from io import BytesIO
import random
from PIL import Image


def generate_minecraft_bottle(width: int = 16, height: int = 24) -> BytesIO:
    """Generate a pixel-art bottle similar to Minecraft style with random liquid color."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    pixels = img.load()
    
    predefined_colors = [
        (255, 50, 50, 255), (255, 100, 100, 255), (200, 0, 0, 255),
        (50, 100, 255, 255), (100, 150, 255, 255), (0, 50, 200, 255),
        (50, 255, 50, 255), (100, 255, 100, 255), (0, 200, 50, 255),
        (255, 200, 50, 255), (255, 150, 0, 255), (255, 255, 100, 255),
        (200, 50, 255, 255), (150, 0, 200, 255), (255, 100, 255, 255),
        (50, 255, 255, 255), (0, 200, 200, 255), (100, 255, 255, 255),
        (255, 0, 127, 255), (127, 0, 255, 255), (255, 127, 0, 255),
        (0, 255, 127, 255), (127, 255, 0, 255), (255, 255, 0, 255),
        (255, 0, 255, 255), (0, 255, 255, 255),
    ]
    
    if random.random() < 0.7:
        liquid_color = random.choice(predefined_colors)
    else:
        liquid_color = (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255),
            255
        )
    
    glass_color = (220, 230, 240, 180)
    glass_dark = (180, 190, 200, 200)
    cork_color = (139, 90, 60, 255)
    cork_dark = (100, 60, 40, 255)
    
    center_x = width // 2
    
    # Stopper/cork (top 3 rows)
    for y in range(0, 3):
        for x in range(center_x - 2, center_x + 3):
            if 0 <= x < width:
                pixels[x, y] = cork_color if x != center_x - 2 and x != center_x + 2 else cork_dark
    
    # Neck (rows 3-6)
    for y in range(3, 7):
        for x in range(center_x - 2, center_x + 3):
            if 0 <= x < width:
                pixels[x, y] = glass_dark if x == center_x - 2 or x == center_x + 2 else glass_color
    
    # Body (rows 7 to height-3)
    body_start = 7
    body_end = height - 3
    body_width = min(width - 2, 12)
    
    for y in range(body_start, body_end):
        half_width = body_width // 2
        for x in range(center_x - half_width, center_x + half_width + 1):
            if 0 <= x < width:
                if x == center_x - half_width or x == center_x + half_width:
                    pixels[x, y] = glass_dark
                elif y > body_start + 2:
                    pixels[x, y] = liquid_color
                else:
                    pixels[x, y] = glass_color
    
    # Bottom (rounded)
    bottom_y = height - 3
    for y in range(bottom_y, height):
        half_width = body_width // 2 - (y - bottom_y)
        for x in range(center_x - half_width, center_x + half_width + 1):
            if 0 <= x < width and half_width > 0:
                if x == center_x - half_width or x == center_x + half_width:
                    pixels[x, y] = glass_dark
                else:
                    pixels[x, y] = liquid_color
    
    img_scaled = img.resize((width * 4, height * 4), Image.NEAREST)
    
    output = BytesIO()
    img_scaled.save(output, format='PNG')
    output.seek(0)
    
    return output
