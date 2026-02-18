import PyInstaller.__main__
import os

# [Note] : Generation of Icons at first
import create_icons
create_icons.create_app_icon()
create_icons.create_file_icon()

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

print(f"📂 Project Root: {project_root}")
print("🚀 Building MPGIF Reader.exe ...")

args = [
    script_path,
    '--name=MPGIF Reader',
    '--onefile',
    '--windowed',
    f'--icon={icon_path}',
    f'--add-data={web_path};web',
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=imageio_ffmpeg',
]

try:
    PyInstaller.__main__.run(args)
    print("\n✅ Build Successful!")
    print(f"👉 Executable located at: {os.path.abspath('dist/MPGIF Reader.exe')}")
    print("⚠️  IMPORTANT: Copy 'ffmpeg.exe' to the same folder as the .exe if you want portable video support!")
except Exception as e:
    print(f"\n❌ Build Failed: {e}")
