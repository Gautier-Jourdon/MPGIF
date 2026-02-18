import cv2
import os
import shutil
import tempfile
import subprocess
from PIL import Image
from fichier.mpgif_structure import MPGIFWriter, MPGIFReader
from compresseur.multimedia_utils import compress_frame_webp, compress_audio_mp3, extract_audio_from_video, get_ffmpeg_cmd, create_delta_image
from fichier.mpgif_structure import MPGIFWriter, MPGIFReader, CODEC_MP3

def video_to_mpgif(input_path, output_path, target_fps=15, width=480, height=None, quality=75, loop=0, progress_callback=None):
    """
    Converts a video file (MP4, WebM, GIF) to .mpgif.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    temp_dir = tempfile.mkdtemp()
    try:
        print(f"🔄 Processing {input_path}...")
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
             pass 

        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) 
        if height is None:
            ratio = width / orig_width
            height = int(orig_height * ratio)

        audio_temp_path = os.path.join(temp_dir, "audio.wav")
        audio_data = None
        try:
            extract_audio_from_video(input_path, audio_temp_path)
            if os.path.exists(audio_temp_path):
                print("🎵 Compressing Audio (MP3)...")
                audio_data = compress_audio_mp3(audio_temp_path)
        except Exception as e:
            print(f"⚠️ Audio extraction failed (might be silent video): {e}")

        writer = MPGIFWriter(output_path, width, height, target_fps, loop)
        if audio_data:
            writer.set_audio(audio_data, codec=CODEC_MP3)

        print("🖼️ Extracting and Compressing Frames...")
        frame_interval = int(cap.get(cv2.CAP_PROP_FPS) / target_fps)
        if frame_interval < 1: frame_interval = 1
        
        count = 0
        saved_count = 0

        import time
        start_time = time.time()
        total_frames_target = int(total_frames / frame_interval) if frame_interval > 0 else 0
        if total_frames_target == 0: total_frames_target = 1

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if count % frame_interval == 0:
                frame = cv2.resize(frame, (width, height))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                
                webp_data = compress_frame_webp(pil_img, quality=quality)
                writer.add_frame(webp_data)
                
                saved_count += 1
                
                if progress_callback:
                    elapsed = time.time() - start_time
                    if saved_count > 0:
                        avg_time_per_frame = elapsed / saved_count
                        remaining_frames = total_frames_target - saved_count
                        eta = remaining_frames * avg_time_per_frame
                        progress = (saved_count / total_frames_target) * 100
                        progress_callback(saved_count, total_frames_target, elapsed, eta)

            count += 1
            
        cap.release()
        
        writer.write()
        print(f"✨ Conversion completed : {output_path} ({saved_count} frames)")
        
    finally:
        shutil.rmtree(temp_dir)

def mpgif_to_video(input_path, output_path):
    """
    Converts .mpgif back to MP4 (h264/aac).
    """
    reader = MPGIFReader(input_path)
    reader.read()
    
    temp_dir = tempfile.mkdtemp()
    try:
        frame_paths = []
        print(f"📂 Extracting {len(reader.frames)} frames...")
        for i, frame_data in enumerate(reader.frames):
            frame_path = os.path.join(temp_dir, f"frame_{i:04d}.webp")
            with open(frame_path, 'wb') as f:
                f.write(frame_data)
            frame_paths.append(frame_path)
            
        audio_path = None
        if reader.audio_data and len(reader.audio_data) > 0:
            print("🎵 Extracting Audio...")
            ext = ".mp3" if reader.audio_codec == CODEC_MP3 else ".opus"
            audio_path = os.path.join(temp_dir, f"audio{ext}")
            with open(audio_path, 'wb') as f:
                f.write(reader.audio_data)
        
        print("🎥 Muxing to Video...")
        frames_pattern = os.path.join(temp_dir, "frame_%04d.webp").replace("\\", "/")
        
        cmd = [
            get_ffmpeg_cmd(), '-y',
            '-framerate', str(reader.fps), 
            '-i', frames_pattern,
        ]
        
        if audio_path:
            cmd.extend(['-i', audio_path])
        
        cmd.extend([
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
        ])
        
        if audio_path:
            cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        cmd.append(output_path)
        
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            print(f"✨ Restored video: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg Muxing Failed!")
            print(f"Error Code: {e.returncode}")
            try:
                print(f"FFmpeg Output:\n{e.stderr.decode('utf-8')}")
            except:
                print(f"FFmpeg Output (raw): {e.stderr}")
            raise e

    finally:
        shutil.rmtree(temp_dir)
