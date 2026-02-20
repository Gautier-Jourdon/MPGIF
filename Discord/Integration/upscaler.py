import os
import sys
import tempfile
import urllib.request
import zipfile
import subprocess
import base64

# Cache paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, '.cache')
UPSCALER_DIR = os.path.join(CACHE_DIR, 'upscalers')

os.makedirs(UPSCALER_DIR, exist_ok=True)

# URLs for Windows portable ncnn-vulkan binaries
BINARIES = {
    "waifu2x": {
        "url": "https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-windows.zip",
        "dir": "waifu2x-ncnn-vulkan-20220728-windows",
        "exe": "waifu2x-ncnn-vulkan.exe"
    },
    "realesrgan": {
        "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip",
        "dir": "realesrgan-ncnn-vulkan-20220424-windows",
        "exe": "realesrgan-ncnn-vulkan.exe"
    }
}

def ensure_binary(model):
    """
    Downloads and extracts the required ncnn-vulkan binary if not locally cached.
    """
    if model not in BINARIES:
        raise ValueError(f"Unknown upscaler model: {model}")
        
    cfg = BINARIES[model]
    target_dir = os.path.join(UPSCALER_DIR, cfg["dir"])
    exe_path = os.path.join(target_dir, cfg["exe"])
    
    # Check if executable already exists
    if os.path.exists(exe_path):
        return exe_path
        
    print(f"[{model.capitalize()}] Binary not found. Downloading from Github...")
    
    zip_path = os.path.join(UPSCALER_DIR, f"{model}.zip")
    try:
        urllib.request.urlretrieve(cfg["url"], zip_path)
        print(f"[{model.capitalize()}] Download complete. Extracting...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(UPSCALER_DIR)
            
        print(f"[{model.capitalize()}] Ready!")
    except Exception as e:
        raise Exception(f"Failed to download/extract {model}: {e}")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
    return exe_path

def upscale_image_base64(image_url, model="waifu2x", scale=2):
    """
    Downloads raw image, upscales it using ncnn-vulkan, and returns Base64.
    """
    exe_path = ensure_binary(model)
    
    scale = int(scale)
    if scale not in [2, 4]:
        scale = 2
        
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "input.png")
        output_path = os.path.join(temp_dir, "output.png")
        
        # 1. Download Input Image
        try:
            req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(input_path, 'wb') as out_file:
                out_file.write(response.read())
        except Exception as e:
            raise Exception(f"Failed to download input image: {e}")
            
        # 2. Build Subprocess Command
        # Models generally reside in the 'models' subdirectory of the extracted folder
        if model == "waifu2x":
            cmd = [
                exe_path,
                "-i", input_path,
                "-o", output_path,
                "-s", str(scale),
                "-n", "2" # Denoise level 2 is usually good for Avatars
            ]
        elif model == "realesrgan":
            # Realesrgan standard model is realesr-animevideov3
            cmd = [
                exe_path,
                "-i", input_path,
                "-o", output_path,
                "-s", str(scale),
                "-n", "realesr-animevideov3" if scale==4 else "realesrgan-x4plus-anime" 
            ]

        # 3. Execute
        try:
            print(f"🚀 Running {model} (x{scale})...")
            # Run in the model's directory so it finds its native '/models' folder payload
            work_dir = os.path.dirname(exe_path)
            result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True, check=True)
            
            if not os.path.exists(output_path):
                raise Exception("Upscaler did not produce an output file.")
                
            # 4. Read to Base64
            with open(output_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                
            return f"data:image/png;base64,{encoded_string}"
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Upscaler execution failed: {e.stderr}")
