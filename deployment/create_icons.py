import os
from PIL import Image, ImageDraw

def create_app_icon():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "app_logo.ico")
    
    if os.path.exists(icon_path):
        print(f"ℹ️ App Icon existing : {icon_path}")
    else:
        # App Icon: Dark Circle with Orange Play
        size = (256, 256)
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Dark Background Circle
        draw.ellipse([(10, 10), (246, 246)], fill="#212121", outline="#ff9800", width=5)
        
        # Orange Play Triangle
        triangle_coords = [(85, 70), (85, 186), (190, 128)]
        draw.polygon(triangle_coords, fill="#ff9800")
        
        img.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print(f"✅ App Icon created : {icon_path}")

def create_file_icon():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "mpgif_logo.ico")
    
    if os.path.exists(icon_path):
        print(f"ℹ️ File Icon existing : {icon_path}")
    else:
        # File Icon: Orange Page/Square
        size = (256, 256)
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Orange Rounded Rect (File shape)
        margin = 40
        draw.rounded_rectangle(
            [(margin, margin), (size[0]-margin, size[1]-margin)],
            radius=30,
            fill="#ff9800",
            outline="white", width=5
        )
        
        # White "GIF" text representation (lines) (Manual pixel font style or blocks)
        # Just simple lines to simulate text
        draw.rectangle([(80, 100), (176, 115)], fill="white")
        draw.rectangle([(80, 130), (176, 145)], fill="white")
        draw.rectangle([(80, 160), (140, 175)], fill="white")
        
        img.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
        print(f"✅ File Icon created : {icon_path}")

if __name__ == "__main__":
    create_app_icon()
    create_file_icon()
