import os
import subprocess
import io
from PIL import Image

import urllib.request
import numpy as np

import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCAL_FFMPEG = os.path.join(BASE_DIR, 'ffmpeg.exe')
FFMPEG_CMD = None

def download_ffmpeg():
    """Downloads a static FFmpeg binary for Windows."""
    url = "https://github.com/imageio/imageio-binaries/raw/master/ffmpeg/ffmpeg-win64-v4.2.2.exe"
    try:
        dest = os.path.join(BASE_DIR, 'ffmpeg.exe')
        print(f"⬇️ Downloading FFmpeg from {url}...")
        urllib.request.urlretrieve(url, dest)
        return dest
    except Exception as e:
        print(f"❌ Error downloading FFmpeg: {e}")
        return None

import shutil

def get_ffmpeg_cmd():
    global FFMPEG_CMD
    if FFMPEG_CMD: return FFMPEG_CMD
        
    # Check if a native ffmpeg binary exists in PATH (Linux/Render)
    if shutil.which('ffmpeg'):
        FFMPEG_CMD = 'ffmpeg'
        return FFMPEG_CMD
        
    if os.path.exists(LOCAL_FFMPEG):
        FFMPEG_CMD = LOCAL_FFMPEG
        return FFMPEG_CMD
        
    try:
        import imageio_ffmpeg
        FFMPEG_CMD = imageio_ffmpeg.get_ffmpeg_exe()
        return FFMPEG_CMD
    except ImportError:
        pass
        
    # Windows native fallback
    if os.name == 'nt':
        downloaded_path = download_ffmpeg()
        if downloaded_path:
            FFMPEG_CMD = downloaded_path
            return FFMPEG_CMD
    
    return 'ffmpeg'

def create_delta_image(curr_img: Image.Image, prev_img: Image.Image, threshold=30) -> Image.Image:
    """
    Creates a delta image (RGBa) where pixels similar to prev_img are transparent.
    """
    curr_arr = np.array(curr_img.convert("RGB"))
    prev_arr = np.array(prev_img.convert("RGB"))
    
    diff = np.abs(curr_arr.astype(int) - prev_arr.astype(int)).astype(np.uint8)
    
    mask = np.any(diff > threshold, axis=2)
    
    delta_arr = np.zeros((curr_arr.shape[0], curr_arr.shape[1], 4), dtype=np.uint8)
    delta_arr[:, :, :3] = curr_arr
    delta_arr[:, :, 3] = mask * 255
    
    return Image.fromarray(delta_arr)

def compress_frame_webp(image: Image.Image, quality=80, lossless=False) -> bytes:
    """
    Compress a PIL Image to WebP bytes.
    """
    output = io.BytesIO()
    image.save(output, format="WEBP", quality=quality, lossless=lossless, method=6)
    return output.getvalue()

def decompress_frame_webp(webp_data: bytes) -> Image.Image:
    """
    Decompress WebP bytes to a PIL Image.
    """
    return Image.open(io.BytesIO(webp_data))

def extract_audio_from_video(video_path: str, output_audio_path: str):
    """
    Extracts audio from video file to a temporary wav/mp3 file using FFmpeg.
    """
    cmd = [
        get_ffmpeg_cmd(), '-y',
        '-i', video_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '44100',
        '-ac', '2',
        output_audio_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def compress_audio_mp3(input_audio_path: str) -> bytes:
    """
    Compresses an audio file to MP3 bytes using FFmpeg.
    Returns the raw bytes of the MP3 file.
    """
    output_temp = input_audio_path + ".mp3"
    
    try:
        cmd = [
            get_ffmpeg_cmd(), '-y',
            '-i', input_audio_path,
            '-c:a', 'libmp3lame',
            '-q:a', '4',
            output_temp
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        with open(output_temp, 'rb') as f:
            mp3_data = f.read()
            
        return mp3_data
    except Exception as e:
        print(f"Erreur compression MP3: {e}")
        return None
    finally:
        if os.path.exists(output_temp):
            os.remove(output_temp)

    """
    Saves audio bytes to a file (e.g., .opus).
    """
    with open(output_path, 'wb') as f:
        f.write(audio_data)

def normalize_audio(input_path: str, output_path: str, target_lufs=-18.0, true_peak=-1.0):
    """
    Normalizes audio using ffmpeg loudnorm filter.
    Target: -18 LUFS (Integrated), -1 dBTP (True Peak).
    """
    try:
        cmd = [
            get_ffmpeg_cmd(), '-y',
            '-i', input_path,
            '-af', f'loudnorm=I={target_lufs}:TP={true_peak}:LRA=11',
            '-ar', '44100',
            output_path
        ]
        # First pass normalization (sufficient for most web use cases without dual-pass)
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception as e:
        print(f"⚠️ Audio normalization failed: {e}")
        return False
