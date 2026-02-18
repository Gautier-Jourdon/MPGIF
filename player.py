import os
import sys
import tempfile
import pygame
import io
import shutil
import subprocess
from PIL import Image
from fichier.mpgif_structure import MPGIFReader

def play_mpgif(filename):
    if not os.path.exists(filename):
        print(f"Existing file : {filename}")
        return

    print(f"📂 Loading of {filename}...")
    reader = MPGIFReader(filename)
    reader.read()
    
    pygame.init()
    screen = pygame.display.set_mode((reader.width, reader.height))
    pygame.display.set_caption(f"MPGIF Player - {filename}")
    clock = pygame.time.Clock()

    print("Pre-rendering frames...")
    frames = []
    for frame_data in reader.frames:
        pil_image = Image.open(io.BytesIO(frame_data)).convert("RGB")
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()
        py_image = pygame.image.fromstring(data, size, mode)
        frames.append(py_image)
    
    temp_dir = tempfile.mkdtemp()
    try:
        audio_cleanup = True
        if reader.audio_data and len(reader.audio_data) > 0:
            audio_opus = os.path.join(temp_dir, "temp.opus")
            audio_wav = os.path.join(temp_dir, "temp.wav")
            
            with open(audio_opus, "wb") as f:
                f.write(reader.audio_data)
            
            subprocess.run([
                'ffmpeg', '-y', '-v', 'quiet',
                '-i', audio_opus,
                audio_wav
            ], check=False)
            
            if os.path.exists(audio_wav):
                try:
                    pygame.mixer.music.load(audio_wav)
                    pygame.mixer.music.play(-1 if reader.loop_count == 0 else reader.loop_count)
                    print("🎵 Audio loaded.")
                except Exception as e:
                    print(f"Audio error: {e}")
        
        running = True
        frame_idx = 0
        
        print("▶️ Reading...")
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            screen.blit(frames[frame_idx], (0, 0))
            pygame.display.flip()
            
            frame_idx = (frame_idx + 1) % len(frames)
            
            clock.tick(reader.fps)
            
    finally:
        pygame.quit()
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python player.py <file.mpgif>")
    else:
        play_mpgif(sys.argv[1])
