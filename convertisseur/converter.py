import cv2
import os
import shutil
import tempfile
import subprocess
from PIL import Image
from fichier.mpgif_structure import MPGIFWriter, MPGIFReader
from compresseur.multimedia_utils import compress_frame_webp, compress_audio_mp3, extract_audio_from_video, get_ffmpeg_cmd, create_delta_image, normalize_audio
from fichier.mpgif_structure import MPGIFWriter, MPGIFReader, CODEC_MP3

PRESETS = {
    "gif-like": {"fps": 12, "width": 320, "quality": 60, "loop": 0, "audio": False},
    "balanced": {"fps": 15, "width": 480, "quality": 75, "loop": 0, "audio": True},
    "hq": {"fps": 24, "width": 720, "quality": 90, "loop": 0, "audio": True},
    "archival": {"fps": 30, "width": 1080, "quality": 95, "loop": 1, "audio": True},
}

def video_to_mpgif(input_path, output_path, preset=None, target_fps=15, width=480, height=None, quality=75, loop=0, metadata=None, progress_callback=None, start_time=None, end_time=None):
    """
    Converts a video file (MP4, WebM, GIF) to .mpgif.
    """
    # Apply Preset if specified
    if preset and preset in PRESETS:
        p = PRESETS[preset]
        target_fps = p['fps']
        width = p['width']
        quality = p['quality']
        loop = p['loop']
        # Audio handling logic below
        
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
        orig_fps = cap.get(cv2.CAP_PROP_FPS) or target_fps
        
        if start_time is not None:
            cap.set(cv2.CAP_PROP_POS_MSEC, float(start_time) * 1000)
        
        # Handle mobile video rotation metadata
        try:
            rotation_meta = int(cap.get(cv2.CAP_PROP_ORIENTATION_META))
        except:
            rotation_meta = 0
            
        if rotation_meta in [90, 270]:
            orig_width, orig_height = orig_height, orig_width
            
        if height is None:
            ratio = width / orig_width
            height = int(orig_height * ratio)

        audio_temp_path = os.path.join(temp_dir, "audio.wav")
        audio_norm_path = os.path.join(temp_dir, "audio_norm.wav")
        audio_data = None
        
        # Audio extraction and normalization
        should_process_audio = True
        if preset and preset in PRESETS and not PRESETS[preset]['audio']:
            should_process_audio = False
            
        if should_process_audio:
            try:
                extract_audio_from_video(input_path, audio_temp_path, start_time=start_time, end_time=end_time)
                if os.path.exists(audio_temp_path):
                    print("🎵 Audio Extracted. Normalizing to -18 LUFS...")
                    if normalize_audio(audio_temp_path, audio_norm_path):
                        print("✅ Normalized. Compressing (MP3)...")
                        audio_data = compress_audio_mp3(audio_norm_path)
                    else:
                        print("⚠️ Normalization failed, using original audio.")
                        audio_data = compress_audio_mp3(audio_temp_path)
            except Exception as e:
                print(f"⚠️ Audio extraction/processing failed: {e}")

        writer = MPGIFWriter(output_path, width, height, target_fps, loop)
        
        # Add Metadata
        if metadata:
            for k, v in metadata.items():
                writer.set_metadata(k, v)
        
        if audio_data:
            writer.set_audio(audio_data, codec=CODEC_MP3)

        print("🖼️ Extracting and Compressing Frames...")
        frame_interval = int(cap.get(cv2.CAP_PROP_FPS) / target_fps)
        if frame_interval < 1: frame_interval = 1
        
        count = 0
        saved_count = 0

        import time
        start_time_exec = time.time()
        
        # Calculate target frames based on start/end time if provided
        actual_fps = cap.get(cv2.CAP_PROP_FPS) or target_fps
        if start_time is not None and end_time is not None:
            frames_to_process = int((end_time - start_time) * actual_fps)
        elif start_time is not None:
            frames_to_process = total_frames - int(start_time * actual_fps)
        elif end_time is not None:
            frames_to_process = int(end_time * actual_fps)
        else:
            frames_to_process = total_frames
            
        total_frames_target = int(frames_to_process / frame_interval) if frame_interval > 0 else 0
        if total_frames_target <= 0: total_frames_target = 1

        while True:
            current_msec = cap.get(cv2.CAP_PROP_POS_MSEC)
            if end_time is not None and current_msec > (end_time * 1000.0):
                break
                
            ret, frame = cap.read()
            if not ret:
                break
            
            if count % frame_interval == 0:
                # Apply rotation if needed
                if rotation_meta == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                elif rotation_meta == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif rotation_meta == 270:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    
                frame = cv2.resize(frame, (width, height))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                
                webp_data = compress_frame_webp(pil_img, quality=quality)
                writer.add_frame(webp_data)
                
                saved_count += 1
                
                if progress_callback:
                    elapsed = time.time() - start_time_exec
                    if saved_count > 0:
                        avg_time_per_frame = elapsed / saved_count
                        remaining_frames = total_frames_target - saved_count
                        eta = remaining_frames * avg_time_per_frame
                        progress = min(99, (saved_count / total_frames_target) * 100) # Cap at 99 so 100% is only on true finish
                        progress_callback(saved_count, total_frames_target, elapsed, eta, progress=progress)

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
