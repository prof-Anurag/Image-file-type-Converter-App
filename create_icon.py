#!/usr/bin/env python3
"""
Create a simple app icon for the Image Converter.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    """Create a simple app icon"""
    
    # Create a new image with a gradient background
    size = 256
    image = Image.new('RGB', (size, size), color='#1f538d')
    draw = ImageDraw.Draw(image)
    
    # Create a subtle gradient effect
    for i in range(size):
        alpha = int(255 * (1 - i / size) * 0.3)
        color = (31 + alpha//4, 83 + alpha//4, 141 + alpha//4)
        draw.line([(0, i), (size, i)], fill=color)
    
    # Draw a rounded rectangle background
    margin = 20
    corner_radius = 30
    
    # Create rounded rectangle
    rect_coords = [margin, margin, size - margin, size - margin]
    draw.rounded_rectangle(rect_coords, corner_radius, fill='#4a9eff', outline='#ffffff', width=3)
    
    # Draw conversion arrows
    arrow_color = '#ffffff'
    center_x, center_y = size // 2, size // 2
    
    # Draw image icon (rectangle with corner)
    img_size = 40
    img_x1 = center_x - img_size - 10
    img_y1 = center_y - img_size // 2
    img_x2 = img_x1 + img_size
    img_y2 = img_y1 + img_size
    
    # Left image
    draw.rectangle([img_x1, img_y1, img_x2, img_y2], fill=arrow_color, outline='#cccccc', width=2)
    draw.polygon([img_x2-12, img_y1, img_x2, img_y1, img_x2, img_y1+12], fill='#cccccc')
    
    # Arrow
    arrow_width = 30
    arrow_y = center_y
    arrow_start_x = img_x2 + 8
    arrow_end_x = arrow_start_x + arrow_width
    
    # Arrow shaft
    draw.line([(arrow_start_x, arrow_y), (arrow_end_x - 8, arrow_y)], fill=arrow_color, width=4)
    
    # Arrow head
    draw.polygon([
        (arrow_end_x - 8, arrow_y - 8),
        (arrow_end_x, arrow_y),
        (arrow_end_x - 8, arrow_y + 8)
    ], fill=arrow_color)
    
    # Right image
    img_x3 = arrow_end_x + 8
    img_x4 = img_x3 + img_size
    draw.rectangle([img_x3, img_y1, img_x4, img_y2], fill=arrow_color, outline='#cccccc', width=2)
    draw.polygon([img_x4-12, img_y1, img_x4, img_y1, img_x4, img_y1+12], fill='#cccccc')
    
    # Add text
    try:
        font_size = 24
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
            
        text = "IMG"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        text_x = (size - text_width) // 2
        text_y = center_y + img_size // 2 + 15
        
        draw.text((text_x, text_y), text, fill='#ffffff', font=font)
        
    except Exception as e:
        print(f"Could not add text: {e}")
    
    # Save multiple sizes
    icon_sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for icon_size in icon_sizes:
        resized = image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Save as ICO file
    ico_path = os.path.join(os.path.dirname(__file__), "app_icon.ico")
    images[0].save(ico_path, format='ICO', sizes=[(s, s) for s in icon_sizes])
    
    # Also save as PNG
    png_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
    image.save(png_path, format='PNG')
    
    print(f"Icon created: {ico_path}")
    print(f"Icon created: {png_path}")
    
    return ico_path

if __name__ == "__main__":
    create_app_icon()