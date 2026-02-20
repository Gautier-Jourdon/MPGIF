#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🎥 Installing FFmpeg..."
# Download a static build of FFmpeg
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz

# Create a local bin directory and move the binaries there so Python can reach them
mkdir -p /opt/render/project/src/bin
cp ffmpeg-*-static/ffmpeg /opt/render/project/src/bin/
cp ffmpeg-*-static/ffprobe /opt/render/project/src/bin/

# Clean up
rm -rf ffmpeg-*-static*

echo "✅ Build complete!"
