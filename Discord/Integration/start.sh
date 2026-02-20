#!/usr/bin/env bash
# start.sh for Render.com Native Python Deployment
# This script launches both the Discord Bot and the Flask Web Server simultaneously.

# 1. Add our custom FFmpeg binaries to the system PATH
export PATH="/opt/render/project/src/bin:$PATH"

# 2. Start the Discord Bot in the background (&)
echo "🤖 Starting Discord Bot (bot.py)..."
python bot.py &

# 3. Start the Flask Web Server in the foreground using Gunicorn
echo "🌐 Starting Web Server (Gunicorn)..."
# Render requires the web server to bind to 0.0.0.0 and process the $PORT environment variable
gunicorn server:app --bind 0.0.0.0:$PORT
