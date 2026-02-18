# MPGIF - High Efficiency Motion Picture Format

MPGIF is a modern, lightweight animation format designed to bridge the gap between heavy video files and inefficient GIFs. It combines **WebP** image compression with **Opus/MP3** audio encoding to deliver high-quality, sound-enabled animations at a fraction of the size.

![MPGIF Format](deployment/mpgif_logo.ico)

## 🚀 Key Features

*   **Optimized Compression**: Uses WebP for frames and MP3 for audio, offering superior quality-to-size ratio compared to GIF.
*   **Audio Support**: Unlike standard GIFs, MPGIF supports synchronized audio tracks.
*   **Portable Player**: Includes a standalone, lightweight player that requires no installation.
*   **Web Ready**: Comes with a JavaScript decoder (`mpgif_reader.js`) for seamless integration into websites.
*   **Zero-Dependency Mode**: Can automatically download necessary engines (FFmpeg) if missing, or run in a fully portable "frozen" mode.

## 📦 Installation

### Prerequisites
*   Python 3.10+ (for source execution)
*   FFmpeg (optional, auto-downloaded if missing)

### Setup
```bash
git clone https://github.com/your-username/MPGIF.git
cd MPGIF
pip install -r requirements.txt
```

*(Note: `requirements.txt` should include `opencv-python`, `numpy`, `pygame`, `pillow`, `imageio`, `imageio-ffmpeg`)*

## 🛠 Usage

You can run the application via the command line or use the built-in GUI.

### Graphical Interface (Recommended)
Simply double-click `MPGIF Reader.exe` (if built) or run:
```bash
python main.py
```
This launches a user-friendly hub to Play, Convert, or Decode files.

### Command Line Interface

**1. Encode a Video to MPGIF**
```bash
python main.py encode "input.mp4" "output.mpgif" --fps 15 --width 480 --quality 75
```

**2. Play an MPGIF**
```bash
python main.py play "animation.mpgif"
```

**3. Decode MPGIF back to MP4**
```bash
python main.py decode "animation.mpgif" "output.mp4"
```

## 🏗 Building from Source

To create a standalone `.exe` for Windows distribution:

1.  **Generate Icons**:
    ```bash
    python deployment/create_icons.py
    ```
2.  **Build Executable**:
    ```bash
    python deployment/build.py
    ```

The resulting `MPGIF Reader.exe` will be found in the `dist/` folder.

## 🌐 Web Integration

To embed an MPGIF on your website:

```html
<canvas id="myCanvas"></canvas>
<script src="web/mpgif_reader.js"></script>
<script>
    const player = new MPGIFReader('animation.mpgif');
    player.load().then(() => {
        player.play(document.getElementById('myCanvas'));
    });
</script>
```

## 📄 Format Specification

MPGIF files follow a custom binary structure:
*   **Header**: Magic string `MPGIF` + Version.
*   **Metadata**: JSON block containing FPS, frame count, width, height, and audio codec info.
*   **Audio Block**: Compressed audio data size + payload.
*   **Frame Index**: Offset table for quick seeking.
*   **Frame Data**: Sequential WebP chunks.

## 📝 License

This project is open-source and available under the Apache 2.0 License.
