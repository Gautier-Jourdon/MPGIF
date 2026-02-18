import os
import sys
import tempfile
import pygame
import io
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog
from PIL import Image
from fichier.mpgif_structure import MPGIFReader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compresseur.multimedia_utils import get_ffmpeg_cmd

class MPGIFPlayer:
    def __init__(self, filename=None):
        self.filename = filename
        self.temp_dir = tempfile.mkdtemp()
        self.reader = None
        self.frames = []
        self.running = False
        self.paused = False
        self.clock = None
        self.screen = None
        
    def select_file(self):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Ouvrir un fichier .mpgif",
            filetypes=[("Fichiers MPGIF", "*.mpgif"), ("Tous les fichiers", "*.*")]
        )
        return file_path

    def load(self):
        if not self.filename:
            self.filename = self.select_file()
            
        if not self.filename or not os.path.exists(self.filename):
            print("Aucun fichier sélectionné ou fichier introuvable.")
            return False

        print(f"📂 Chargement de {self.filename}...")
        self.reader = MPGIFReader(self.filename)
        self.reader.read()
        return True

    def prepare_assets(self):
        print("🖼️ Préparation des frames...")
        for frame_data in self.reader.frames:
            pil_image = Image.open(io.BytesIO(frame_data)).convert("RGB")
            mode = pil_image.mode
            size = pil_image.size
            data = pil_image.tobytes()
            py_image = pygame.image.fromstring(data, size, mode)
            self.frames.append(py_image)

        if self.reader.audio_data and len(self.reader.audio_data) > 0:
            audio_ext = ".mp3" if self.reader.audio_codec == 3 else ".opus"
            audio_temp = os.path.join(self.temp_dir, f"temp{audio_ext}")
            
            with open(audio_temp, "wb") as f:
                f.write(self.reader.audio_data)
            
            try:
                pygame.mixer.music.load(audio_temp)
                print(f"🎵 Audio {audio_ext} chargé (Direct).")
            except Exception as e:
                print(f"⚠️ Échec chargement direct audio ({e}). Tentative conversion FFmpeg...")
                audio_wav = os.path.join(self.temp_dir, "temp.wav")
                try:
                    subprocess.run([
                        get_ffmpeg_cmd(), '-y', '-v', 'error',
                        '-i', audio_temp,
                        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                        audio_wav
                    ], check=True)
                    
                    if os.path.exists(audio_wav):
                        pygame.mixer.music.load(audio_wav)
                        print("🎵 Audio chargé (via conversion WAV).")
                except FileNotFoundError:
                     print("❌ FFmpeg introuvable et échec lecture directe. Pas de son.")
                except Exception as ex:
                     print(f"❌ Erreur son finale: {ex}")

    def run(self):
        if not self.load():
            return

        pygame.init()
        self.screen = pygame.display.set_mode((self.reader.width, self.reader.height))
        pygame.display.set_caption(f"MPGIF Player - {os.path.basename(self.filename)}")
        self.clock = pygame.time.Clock()
        
        self.prepare_assets()
        
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy() == False:
            if self.reader.audio_data and len(self.reader.audio_data) > 0:
                 try:
                     loops = -1 if self.reader.loop_count == 0 else (self.reader.loop_count - 1 if self.reader.loop_count > 0 else 0)
                     if self.reader.loop_count == 1: loops = 0

                     pygame.mixer.music.play(loops=loops)
                 except Exception as e:
                     print(f"❌ Erreur lecture audio: {e}")

        self.running = True
        frame_idx = 0
        
        print("▶️ Lecture (Espace: Pause/Play, Echap: Quitter)")
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                        if self.paused:
                            if pygame.mixer.music.get_busy():
                                pygame.mixer.music.pause()
                            pygame.display.set_caption(f"MPGIF Player - {os.path.basename(self.filename)} [PAUSE]")
                        else:
                            if pygame.mixer.music.get_busy() or (self.reader.audio_data and len(self.reader.audio_data) > 0):
                                pygame.mixer.music.unpause()
                            pygame.display.set_caption(f"MPGIF Player - {os.path.basename(self.filename)}")

            if not self.paused:
                if self.frames:
                    self.screen.blit(self.frames[frame_idx], (0, 0))
                    frame_idx = (frame_idx + 1) % len(self.frames)
                
                pygame.display.flip()
                self.clock.tick(self.reader.fps)
            else:
                self.clock.tick(10)

        self.cleanup()

    def cleanup(self):
        pygame.quit()
        shutil.rmtree(self.temp_dir)
        print("Fermeture du lecteur.")

if __name__ == "__main__":
    import sys
    fname = sys.argv[1] if len(sys.argv) > 1 else None
    player = MPGIFPlayer(fname)
    player.run()
