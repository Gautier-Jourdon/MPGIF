#!/usr/bin/env bash

export PATH="/opt/render/project/src/bin:$PATH"

echo "🤖 Starting Discord Bot (bot.py)..."
python -u bot.py &

echo "🌐 Starting Web Server (Gunicorn)..."
gunicorn server:app --bind 0.0.0.0:$PORT
