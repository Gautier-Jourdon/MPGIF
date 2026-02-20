import os
import subprocess
import shutil
import tempfile
import sys
import glob

# Ensure we can import MPGIFReader
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from fichier.mpgif_structure import MPGIFReader

def transcode_to_mp4(mpgif_path, output_path):
    """
    Converts an MPGIF file to MP4 using FFmpeg.
    Returns the path to the MP4 file (output_path).
    """
    
    if os.path.exists(output_path):
        return output_path

    print(f"🔄 Transcoding {os.path.basename(mpgif_path)} to MP4...")
    
    # Create temp directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            reader = MPGIFReader(mpgif_path)
            reader.read()
            
            if not reader.frames:
                raise ValueError("No frames found in MPGIF")
                
            # 1. Extract Frames
            for i, frame_data in enumerate(reader.frames):
                # Save as WebP
                frame_name = os.path.join(temp_dir, f"frame_{i:04d}.webp")
                with open(frame_name, 'wb') as f:
                    f.write(frame_data)
            
            # 2. Extract Audio
            audio_path = None
            if reader.audio_data:
                # determine extension based on codec? 
                # reader.audio_codec: 1=Opus, 2=AAC. 
                # But ffmpeg detects usually. Let's assume raw or container?
                # The writer writes raw packets often? 
                # Let's try saving as .bin and let ffmpeg guess or assuming it's what loudnorm produced (aac/opus frames)
                # Actually converter.py writes raw data from the container. 
                # If it's pure data, ffmpeg might need headers.
                # Let's try .aac or .opus
                ext = "opus" if reader.audio_codec == 1 else "aac" # Simplified guess
                audio_path = os.path.join(temp_dir, f"audio.{ext}")
                with open(audio_path, 'wb') as f:
                    f.write(reader.audio_data)

            # 3. Assemble with FFmpeg
            # Locate ffmpeg.exe in project root (../../ffmpeg.exe relative to this script)
            # current_dir is Discord/Integration
            project_root = os.path.dirname(os.path.dirname(current_dir))
            ffmpeg_path = os.path.join(project_root, 'ffmpeg.exe')
            
            if not os.path.exists(ffmpeg_path):
                 # Fallback to system path
                 ffmpeg_path = 'ffmpeg'
                 
            cmd = [
                ffmpeg_path,
                '-y', # Overwrite
                '-framerate', str(reader.fps),
                '-i', os.path.join(temp_dir, 'frame_%04d.webp'),
            ]
            
            if audio_path:
                cmd.extend(['-i', audio_path])
                
            cmd.extend([
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p', # Critical for Discord compatibility
                '-movflags', '+faststart',
                '-vf', "scale=trunc(iw/2)*2:trunc(ih/2)*2", # Ensure dimensions are even
            ])
            
            if audio_path:
                cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
            
            cmd.append(output_path)
            
            # Run
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"✅ Transcoding complete: {output_path}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg Error: {e.stderr.decode()}")
            raise e
        except Exception as e:
            print(f"❌ Transcoding Error: {e}")
            raise e
            
    return output_path

def transcode_to_gif_audio(mpgif_path, output_base):
    """
    Converts MPGIF to a .gif file (Visual) and a .mp3 file (Audio).
    Returns (gif_path, audio_path).
    """
    gif_path = output_base + ".gif"
    audio_path_out = output_base + ".mp3"
    
    # Check cache
    if os.path.exists(gif_path) and os.path.exists(audio_path_out):
        return gif_path, audio_path_out
        
    print(f"🔄 Splitting {os.path.basename(mpgif_path)} to GIF + MP3...")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            reader = MPGIFReader(mpgif_path)
            reader.read()
            
            # 1. Extract Frames
            for i, frame_data in enumerate(reader.frames):
                with open(os.path.join(temp_dir, f"frame_{i:04d}.webp"), 'wb') as f:
                    f.write(frame_data)
            
            # 2. Extract Temp Audio
            temp_audio = None
            if reader.audio_data:
                ext = "opus" if reader.audio_codec == 1 else "aac"
                temp_audio = os.path.join(temp_dir, f"temp_audio.{ext}")
                with open(temp_audio, 'wb') as f:
                    f.write(reader.audio_data)

            # 3. Create GIF (Visual Loop)
            # Use basic ffmpeg gif encoding
            cmd_gif = [
                'ffmpeg', '-y',
                '-framerate', str(reader.fps),
                '-i', os.path.join(temp_dir, 'frame_%04d.webp'),
                '-vf', "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse", # Better quality
                '-loop', '0', # Infinite loop
                gif_path
            ]
            subprocess.run(cmd_gif, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            
            # 4. Create MP3 (Audio)
            has_audio = False
            if temp_audio:
                cmd_audio = [
                    'ffmpeg', '-y',
                    '-i', temp_audio,
                    '-vn', # No video
                    '-acodec', 'libmp3lame',
                    '-q:a', '2',
                    audio_path_out
                ]
                subprocess.run(cmd_audio, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                has_audio = True
            else:
                # Create silent mp3? Check what user wants.
                # Usually if no audio, we just return None for audio path
                pass
                
            return gif_path, (audio_path_out if has_audio else None)

        except Exception as e:
            print(f"❌ Split Error: {e}")
            raise e

if __name__ == "__main__":
    # Test
    if len(sys.argv) > 1:
        src = sys.argv[1]
        dest = src + ".mp4"
        transcode_to_mp4(src, dest)
