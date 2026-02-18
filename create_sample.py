import numpy as np
import cv2
from PIL import Image
from fichier.mpgif_structure import MPGIFWriter, CODEC_OPUS
from compresseur.multimedia_utils import compress_frame_webp

def create_sample(filename="sample.mpgif"):
    width, height = 320, 240
    fps = 15
    duration = 2 # seconds
    
    writer = MPGIFWriter(filename, width, height, fps)
    
    # Metadata
    writer.set_metadata("title", "Procedural Sample")
    writer.set_metadata("author", "MPGIF Builder")
    writer.set_metadata("tags", "test,generated,python")
    
    print(f"Generating {duration}s sample...")
    
    for i in range(fps * duration):
        # Create a moving circle
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Background gradient
        for y in range(height):
            frame[y, :, 0] = y % 255  # Blue gradient
            
        # Circle
        t = i / (fps * duration)
        cx = int(width * t)
        cy = int(height/2 + 50 * np.sin(t * 10))
        cv2.circle(frame, (cx, cy), 30, (0, 255, 255), -1) # Yellow circle
        
        # Text
        cv2.putText(frame, f"Frame {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Convert to WebP
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        webp_data = compress_frame_webp(pil_img, quality=80)
        writer.add_frame(webp_data)

    writer.write()

if __name__ == "__main__":
    create_sample()
