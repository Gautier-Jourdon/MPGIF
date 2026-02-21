from flask import Flask, send_from_directory, request, jsonify, send_file, make_response
import os
import random
import sys
import io
import json
import mimetypes
import uuid # For generating unique task IDs

# Global in-memory task tracker for long conversions
progress_tracker = {}

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, continuing without local .env loading.")

from supabase import create_client, Client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

if not supabase:
    print("⚠️  WARNING: SUPABASE_URL or SUPABASE_KEY is missing from environment. Database connection will fail.")
else:
    print("✅ Supabase client initialized.")

# Setup paths (Adjust based on your folder structure)
# Assuming this script is in Discord/Integration/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
sys.path.append(BASE_DIR) # Add project root to path for imports 
WEB_DIR = os.path.join(BASE_DIR, 'web')
FILES_DIR = os.path.join(BASE_DIR, 'mpgifs') # You will need to create this folder and put .mpgif files in it

app = Flask(__name__, static_folder=WEB_DIR)

print(f"📂 Serving MPGIFs from: {FILES_DIR}")
print(f"🌐 Serving Web from: {WEB_DIR}")

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)
    print(f"⚠️ Created missing directory: {FILES_DIR}")

@app.route('/')
def home():
    return "MPGIF Server is Running! Use /view?file=filename.mpgif"

@app.route('/v/<filename>')
def embed_player(filename):
    """Serve a minimal HTML page to display the MPGIF in full screen."""
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>MPGIF - {filename}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body, html {{ margin: 0; padding: 0; background: #0b0f19; height: 100vh; display: flex; align-items: center; justify-content: center; overflow: hidden; font-family: 'Courier New', monospace; }}
        canvas {{ max-width: 100%; max-height: 100vh; object-fit: contain; cursor: pointer; }}
        #hud {{ position: absolute; bottom: 20px; color: rgba(129, 212, 250, 0.5); font-size: 12px; pointer-events: none; }}
    </style>
</head>
<body>
    <canvas id="playerCanvas" title="Click to Play/Pause"></canvas>
    <div id="hud">MPGIF RAW STREAM</div>
    <script src="/mpgif_reader.js"></script>
    <script src="/mpgif_player.js"></script>
    <script>
        const canvas = document.getElementById('playerCanvas');
        const pl = new MPGIFPlayer(canvas);
        let loaded = false;
        canvas.onclick = () => {{
            if (!loaded) {{
                pl.load('/files/{filename}').then(() => {{
                    loaded = true; pl.play();
                }}).catch(e => console.error(e));
            }} else {{
                if (pl.isPlaying) pl.stop(); else pl.play();
            }}
        }};
        pl.load('/files/{filename}').then(() => loaded = true);
    </script>
</body>
</html>'''
    return html

@app.route('/view')
def view():
    filename = request.args.get('file', '')
    # Extract basename if it's a path like /files/foo.mpgif
    basename = os.path.basename(filename) if filename else "Unknown"
    
    # Get Public URL for image
    # Note: request.url_root gives http://localhost:5000/ or ngrok url
    # We need the full URL for Discord to display the image
    base_url = request.url_root.rstrip('/')
    # If filename is just "foo.mpgif", construct /api/thumbnail/foo.mpgif
    # If it is /files/foo.mpgif, extract foo.mpgif
    clean_name = basename
    
    image_url = f"{base_url}/api/thumbnail/{clean_name}"
    
    # Load HTML
    try:
        with open(os.path.join(WEB_DIR, 'view.html'), 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Replace
        content = content.replace('{{TITLE}}', clean_name)
        content = content.replace('{{IMAGE_URL}}', image_url)
        return content
    except Exception as e:
        return f"Error loading template: {e}"

@app.route('/<path:filename>.js')
def serve_js(filename):
    return send_from_directory(WEB_DIR, f"{filename}.js")

from flask import redirect

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')

@app.route('/files/<path:filename>')
def get_file(filename):
    if not supabase: return "No DB connection", 500
    public_url = supabase.storage.from_('mpgifs').get_public_url(filename)
    return redirect(public_url)

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(WEB_DIR, filename)

@app.route('/chibi/<path:filename>')
def serve_chibi(filename):
    return send_from_directory(os.path.join(PUBLIC_DIR, 'chibi'), filename)

@app.route('/public/<path:filename>')
def serve_public(filename):
    return send_from_directory(PUBLIC_DIR, filename)

@app.route('/api/thumbnail/<path:filename>')
def get_thumbnail(filename):
    """Serves the thumbnail extracted during upload via Supabase public url."""
    if not supabase: return "No DB connection", 500
    public_url = supabase.storage.from_('mpgifs').get_public_url(filename + '.webp')
    return redirect(public_url)

@app.route('/api/list')
def list_files():
    """Returns a simple list of filenames from Supabase."""
    if not supabase: return jsonify([])
    try:
        res = supabase.table('files').select('filename').execute()
        return jsonify([f['filename'] for f in res.data])
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return jsonify([])

@app.route('/api/search')
def search():
    query = request.args.get('q', '').lower()
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    
    try:
        res = supabase.table('files').select('filename').execute()
        files = [f['filename'] for f in res.data]
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    if query == 'random':
        if files:
            selected = random.choice(files)
            return jsonify({
                "file": selected, 
                "url": f"/files/{selected}",
                "thumbnail": f"/api/thumbnail/{selected}"
            })
        return jsonify({"error": "No files found"}), 404
        
    filtered = [f for f in files if query in f.lower()]
    # Return first match with details for search
    if filtered:
        selected = filtered[0]
        return jsonify({
            "file": selected, 
            "url": f"/files/{selected}",
            "thumbnail": f"/api/thumbnail/{selected}"
        })
        
    return jsonify([])

@app.route('/api/files')
def get_files():
    """Returns list of all MPGIFs with their Metadata from Supabase."""
    if not supabase: return jsonify([])
    try:
        # Fetch files
        files_res = supabase.table('files').select('*').execute()
        db_files = files_res.data
        
        # Fetch all votes to compute score and up/down counts
        votes_res = supabase.table('votes').select('*').execute()
        db_votes = votes_res.data
        
        # Fetch users to get their badges
        users_res = supabase.table('users').select('id, badges').execute()
        users_dict = {str(u['id']): u.get('badges', []) for u in users_res.data}
        all_rules_dict = {r["id"]: r for r in get_all_badge_rules()}
        
        files_out = []
        for f in db_files:
            filename = f['filename']
            uploader_id = str(f.get('uploader_id', ''))
            
            upvotes = [v for v in db_votes if v['filename'] == filename and v['vote_type'] == 'up']
            downvotes = [v for v in db_votes if v['filename'] == filename and v['vote_type'] == 'down']
            score = len(upvotes) - len(downvotes)
            
            uploader_badges = users_dict.get(uploader_id, [])
            card_badges = [all_rules_dict[bid]['icon'] for bid in uploader_badges if bid in all_rules_dict and all_rules_dict[bid].get('show_on_card')]
            
            files_out.append({
                "name": filename,
                "score": score,
                "upvotes": len(upvotes),
                "downvotes": len(downvotes),
                "tags": f.get('tags') or [],
                "width": f.get('width', 0) or 0,
                "height": f.get('height', 0) or 0,
                "uploader_id": uploader_id,
                "uploader_badges": card_badges
            })
            
        # Sort by Score descending
        files_out.sort(key=lambda x: x['score'], reverse=True)
        return jsonify(files_out)
        
    except Exception as e:
        print(f"❌ Error fetching files from Supabase: {e}")
        return jsonify([])

# Authorization
from werkzeug.utils import secure_filename

def get_allowed_ids(env_var):
    ids = os.getenv(env_var, '').split(',')
    return [id.strip() for id in ids if id.strip()]

def is_admin_user(user_id):
    return str(user_id) in get_allowed_ids('ADMIN_IDS')

def is_mod_user(user_id):
    return str(user_id) in get_allowed_ids('MOD_IDS')

def can_manage(user_id):
    """Checks if user is Admin OR Moderator."""
    return is_admin_user(user_id) or is_mod_user(user_id)

@app.route('/api/check_auth')
def check_auth():
    user_id = request.args.get('user_id')
    return jsonify({"can_manage": can_manage(user_id)})

def call_auto_tagger(image_bytes):
    """
    Attempts to generate tags using HF Inference API if token is provided.
    Otherwise, returns fallback tags.
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        # Fallback logic if no API key
        return ["auto-tagged", "ai-pending"]
        
    try:
        import requests
        headers = {"Authorization": f"Bearer {hf_token}"}
        # Lightweight public vision-to-text model
        API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        response = requests.post(API_URL, headers=headers, data=image_bytes)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                caption = result[0]['generated_text']
                # Create rudimentary tags from caption (words > 3 chars)
                words = [w.strip().lower() for w in caption.split(' ') if len(w) > 3]
                tags = list(set(words))[:4]
                tags.append("ai-vision")
                return tags[:5]
    except Exception as e:
        print(f"⚠️ Auto-tagger failed: {e}")
        
    return ["auto-tagged", "error"]

def process_mpgif_upload(temp_path, save_name, user_id, custom_name="", tags_list=[]):
    """Core logic to push a valid .mpgif to Supabase Storage & Postgres."""
    with open(temp_path, 'rb') as f:
        file_bytes = f.read()

    temp_mp4_path = os.path.join(FILES_DIR, save_name + '.mp4')
    width, height = 0, 0
    from fichier.mpgif_structure import MPGIFReader
    import transcoder
    
    try:
        reader = MPGIFReader(temp_path)
        reader.read()
        width, height = reader.width, reader.height
        
        # Upload .mpgif
        try: supabase.storage.from_('mpgifs').upload(file=file_bytes, path=save_name, file_options={"upsert": "true", "content-type": "application/octet-stream"})
        except: supabase.storage.from_('mpgifs').update(file=file_bytes, path=save_name, file_options={"upsert": "true", "content-type": "application/octet-stream"})

        # Upload .webp
        if reader.frames:
            try: supabase.storage.from_('mpgifs').upload(file=reader.frames[0], path=save_name + '.webp', file_options={"upsert": "true", "content-type": "image/webp"})
            except: supabase.storage.from_('mpgifs').update(file=reader.frames[0], path=save_name + '.webp', file_options={"upsert": "true", "content-type": "image/webp"})

        # Upload .mp4
        try:
            transcoder.transcode_to_mp4(temp_path, temp_mp4_path)
            if os.path.exists(temp_mp4_path):
                with open(temp_mp4_path, 'rb') as f_mp4:
                    mp4_bytes = f_mp4.read()
                    try: supabase.storage.from_('mpgifs').upload(file=mp4_bytes, path=save_name + '.mp4', file_options={"upsert": "true", "content-type": "video/mp4"})
                    except: supabase.storage.from_('mpgifs').update(file=mp4_bytes, path=save_name + '.mp4', file_options={"upsert": "true", "content-type": "video/mp4"})
        except Exception as t_err: print(f"Transcode error: {t_err}")

        # AI Vision Auto-Tagging Fallback
        if not tags_list and reader.frames:
            tags_list = call_auto_tagger(reader.frames[0])

        # Postgres Upsert
        supabase.table('files').upsert({
            "filename": save_name, "uploader_id": user_id, "custom_name": custom_name,
            "width": width, "height": height, "tags": tags_list
        }).execute()

        new_badges = update_user_stat(user_id, "uploads")
        return {"status": "ok", "filename": save_name, "badges_earned": new_badges}

    except Exception as ex:
        print(f"Validation/Upload failed: {ex}")
        raise ex
    finally:
        if os.path.exists(temp_mp4_path): os.remove(temp_mp4_path)

@app.route('/api/progress')
def api_progress():
    task_id = request.args.get('task_id')
    if task_id in progress_tracker:
        return jsonify(progress_tracker[task_id])
    return jsonify({"status": "unknown"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    try:
        user_id = request.form.get('user_id')
        custom_name = request.form.get('custom_name')
        raw_tags = request.form.get('tags', '')
        
        tags_list = [t.strip() for t in raw_tags.split(',') if t.strip()]
        if len(tags_list) > 5: tags_list = tags_list[:5] # Max 5 tags
        
        if not can_manage(user_id):
            return jsonify({"error": "Unauthorized"}), 403
            
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if file and file.filename.endswith('.mpgif'):
            if custom_name and custom_name.strip():
                save_name = secure_filename(custom_name.strip())
                if not save_name.lower().endswith('.mpgif'):
                     save_name += '.mpgif'
            else:
                save_name = secure_filename(file.filename)

            file_bytes = file.read()
            temp_path = os.path.join(FILES_DIR, save_name)
            
            # Save temporarily first to validate & extract metadata BEFORE uploading
            with open(temp_path, 'wb') as f:
                f.write(file_bytes)
                
            try:
                res = process_mpgif_upload(temp_path, save_name, user_id, custom_name, tags_list)
                return jsonify(res), 200
            except Exception as ex:
                return jsonify({"error": f"Fichier corrompu ou fausse extension. Veuillez utiliser le Convertisseur. D\u00e9tail: {ex}"}), 400
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)
                
        else:
            return jsonify({"error": "Invalid file type (must be .mpgif)"}), 400
            
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tags/update', methods=['POST'])
def update_tags():
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    try:
        data = request.json
        user_id = data.get('user_id')
        filename = data.get('filename')
        raw_tags = data.get('tags', [])
        
        if not can_manage(user_id):
            return jsonify({"error": "Unauthorized. Only Admins/Mods can regularize tags."}), 403
            
        if not filename:
            return jsonify({"error": "Missing filename"}), 400
            
        tags_list = [str(t).strip() for t in raw_tags if str(t).strip()]
        if len(tags_list) > 5: tags_list = tags_list[:5]
        
        res = supabase.table('files').update({"tags": tags_list}).eq("filename", filename).execute()
        return jsonify({"status": "ok", "tags": tags_list})
        
    except Exception as e:
        print(f"Update tags error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/vote', methods=['POST'])
def handle_vote():
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    try:
        data = request.json
        user_id = str(data.get('user_id'))
        filename = data.get('filename')
        vote_type = data.get('type') # 'up', 'down', or 'none' (remove)
        
        if not user_id or not filename: return jsonify({"error": "Missing data"}), 400
        
        # 1. Remove existing vote
        supabase.table('votes').delete().eq('filename', filename).eq('user_id', user_id).execute()
        
        # 2. Add new vote if not 'none'
        if vote_type in ['up', 'down']:
            supabase.table('votes').insert({
                'filename': filename,
                'user_id': user_id,
                'vote_type': vote_type
            }).execute()
        
        # --- Update Stats ---
        new_badges = []
        if vote_type in ['up', 'down']:
            new_badges = update_user_stat(user_id, "votes")

        # Calculate new score to return
        votes_res = supabase.table('votes').select('*').eq('filename', filename).execute()
        db_votes = votes_res.data
        up = len([v for v in db_votes if v['vote_type'] == 'up'])
        dn = len([v for v in db_votes if v['vote_type'] == 'down'])
        score = up - dn
        
        return jsonify({"status": "ok", "score": score, "badges_earned": new_badges})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete_file():
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    try:
        data = request.json
        user_id = data.get('user_id')
        filename = data.get('filename')
        
        if not can_manage(user_id):
            return jsonify({"error": "Unauthorized"}), 403
            
        if not filename: return jsonify({"error": "Missing filename"}), 400
        if '..' in filename or '/' in filename or '\\' in filename:
             return jsonify({"error": "Invalid filename"}), 400

        # Delete from Supabase Storage (MPGIF and cached MP4)
        supabase.storage.from_('mpgifs').remove([filename, filename+'.mp4'])
        
        # Delete from DB (this cascades to votes and favorites)
        supabase.table('files').delete().eq('filename', filename).execute()
        
        return jsonify({"status": "deleted"}), 200
        
    except Exception as e:
        print(f"Delete error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/catalogue')
def get_catalogue_grid():
    """Generates a 2x2 grid collage of thumbnails for a given page."""
    try:
        page = int(request.args.get('page', 0))
        per_page = 4 # 2x2 grid
        
        if not supabase: return jsonify({"files": [], "has_next": False}), 500

        res = supabase.table('files').select('filename').execute()
        files = sorted([f['filename'] for f in res.data])
        
        total_files = len(files)
        start = page * per_page
        end = start + per_page
        page_files = files[start:end]
        
        # If request asks for JSON list (for the bot to build dropdown)
        if request.args.get('format') == 'json':
            return jsonify({
                "files": page_files,
                "has_next": end < total_files,
                "page": page,
                "image_url": f"/api/catalogue?page={page}&format=image"
            })
            
        # Image Generation
        from PIL import Image, ImageDraw, ImageFont
        import io
        import requests
        
        # Canvas Settings
        thumb_w, thumb_h = 320, 240
        grid_w = thumb_w * 2
        grid_h = thumb_h * 2
        grid_img = Image.new('RGB', (grid_w, grid_h), color=(44, 47, 51)) # Discord Dark BG
        
        draw = ImageDraw.Draw(grid_img)
        
        for idx, filename in enumerate(page_files):
            # Calculate position
            row = idx // 2
            col = idx % 2
            x = col * thumb_w
            y = row * thumb_h
            
            # Load Thumbnail from Supabase
            try:
                public_url = supabase.storage.from_('mpgifs').get_public_url(filename + '.webp')
                r = requests.get(public_url)
                if r.status_code == 200:
                    thumb_bytes = r.content
                    thumb = Image.open(io.BytesIO(thumb_bytes)).convert("RGB")
                    # Resize/Crop to fit slot
                    thumb = thumb.resize((thumb_w, thumb_h))
                    grid_img.paste(thumb, (x, y))
            except Exception as e:
                print(f"Error drawing thumb for {filename}: {e}")
                
            # Draw Label (A, B, C, D) or Number
            label = str(idx + 1)
            # Semi-transparent box for label
            draw.rectangle([x, y, x+30, y+30], fill=(0,0,0,128))
            draw.text((x+10, y+5), label, fill="white")
            
            # Draw Filename at bottom
            draw.rectangle([x, y+thumb_h-20, x+thumb_w, y+thumb_h], fill=(0,0,0,128))
            draw.text((x+5, y+thumb_h-18), filename[:30], fill="white")

        # Serve Image
        img_io = io.BytesIO()
        grid_img.save(img_io, 'JPEG', quality=80)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')

    except Exception as e:
        print(f"Grid error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/browse')
def browse():
    return send_from_directory(WEB_DIR, 'browse.html')

@app.route('/share/<path:filename>')
def share_wrapper(filename):
    """
    Serves an HTML page with Open Graph tags to force Discord to embed the MP4
    as a looping video (GIF-like).
    The URL ends in .gif (e.g. /share/video.gif) to look cool, 
    but the content is text/html.
    """
    real_name = filename.replace('.gif', '.mpgif')
    
    base_url = request.url_root.rstrip('/')
    env_url = os.getenv("SERVER_URL")
    if env_url: base_url = env_url.rstrip('/')
    
    width, height = 640, 480 # Default
    if supabase:
        try:
            res = supabase.table('files').select('width, height').eq('filename', real_name).execute()
            if res.data:
                width = res.data[0].get('width', 640)
                height = res.data[0].get('height', 480)
        except: pass
        
        video_url = supabase.storage.from_('mpgifs').get_public_url(real_name + '.mp4')
        thumb_url = supabase.storage.from_('mpgifs').get_public_url(real_name + '.webp')
    else:
        video_url = f"{base_url}/view?file=/files/{real_name}"
        thumb_url = ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{real_name}</title>
        
        <meta property="og:site_name" content="MPGIF Player" />
        <meta property="og:title" content="{real_name}" />
        <meta property="og:description" content="Click to watch with sound! 🎶" />
        
        <meta property="og:type" content="video.other" />
        <meta property="og:url" content="{base_url}/view?file=/files/{real_name}" />
        <meta property="og:image" content="{thumb_url}" />
        
        <meta property="og:video" content="{video_url}" />
        <meta property="og:video:url" content="{video_url}" />
        <meta property="og:video:secure_url" content="{video_url}" />
        <meta property="og:video:type" content="video/mp4" />
        <meta property="og:video:width" content="{width}" />
        <meta property="og:video:height" content="{height}" />
    </head>
    <body>
        <p>Redirecting...</p>
        <script>window.location.href = "{base_url}/view?file=/files/{real_name}&autoplay=1";</script>
    </body>
    </html>
    """

# --- DISCORD API HELPERS ---
def get_discord_headers():
    return {
        "Authorization": f"Bot {os.getenv('DISCORD_BOT_TOKEN')}",
        "Content-Type": "application/json"
    }

@app.route('/api/channels', methods=['GET'])
def get_guild_channels():
    guild_id = request.args.get('guild_id')
    if not guild_id: return jsonify([])
    
    try:
        url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
        import requests
        r = requests.get(url, headers=get_discord_headers())
        
        if r.status_code == 200:
             channels = r.json()
             text_channels = [{"id": c["id"], "name": c.get("name", "Unknown")} for c in channels if c.get("type", -1) == 0]
             return jsonify(text_channels)
        return jsonify([])
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return jsonify([])

@app.route('/api/guild/info', methods=['GET'])
def get_guild_info():
    guild_id = request.args.get('guild_id')
    if not guild_id: return jsonify({"error": "Missing ID"}), 400
    
    try:
        import requests
        headers = get_discord_headers()
        r = requests.get(f"https://discord.com/api/v10/guilds/{guild_id}?with_counts=true", headers=headers)
        if r.status_code != 200: return jsonify({"error": "Discord API Error"}), r.status_code
        g = r.json()
        
        icon_url = None
        if g.get('icon'):
            icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{g['icon']}.png"
            
        return jsonify({
            "name": g.get('name', 'Unknown'),
            "icon": icon_url,
            "id": guild_id,
            "member_count": g.get('approximate_member_count', g.get('member_count', 0)),
        })
    except Exception as e:
        print(f"Error fetching guild info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/publish', methods=['POST'])
def publish():
    """Receives a request from the web gallery to post a GIF to Discord via Webhook."""
    try:
        data = request.json
        filename = data.get('filename')
        webhook_url = data.get('webhook_url')
        channel_id = data.get('channel_id')
        
        if not filename: return jsonify({"error": "Missing filename"}), 400
        if not supabase: return jsonify({"error": "No DB connection"}), 500
        
        public_mp4_url = supabase.storage.from_('mpgifs').get_public_url(filename + '.mp4')
            
        import requests
        target_url = webhook_url
        
        if channel_id:
            print(f"🔎 Resolving Webhook for Channel {channel_id}...")
            wh_url = f"https://discord.com/api/v10/channels/{channel_id}/webhooks"
            r_wh = requests.get(wh_url, headers=get_discord_headers())
            webhooks = r_wh.json() if r_wh.status_code == 200 else []
            
            found_wh = next((w for w in webhooks if w.get('token')), None)
            
            if found_wh:
                target_url = f"https://discord.com/api/webhooks/{found_wh['id']}/{found_wh['token']}"
            else:
                r_create = requests.post(wh_url, headers=get_discord_headers(), json={"name": "MPGIF Proxy"})
                if r_create.status_code in [200, 201]:
                    new_wh = r_create.json()
                    target_url = f"https://discord.com/api/webhooks/{new_wh['id']}/{new_wh['token']}"

        if not target_url:
             return jsonify({"error": "Could not resolve a valid Webhook URL"}), 400

        print(f"📤 Publishing to: {target_url}")

        file_bytes = None
        try:
            r_vid = requests.get(public_mp4_url, timeout=10)
            if r_vid.status_code == 200:
                file_bytes = r_vid.content
        except Exception as e:
            print(f"Skipping direct bytes upload: {e}")

        base_url = os.environ.get("SERVER_URL", request.url_root.rstrip('/'))
        avatar_url = f"{base_url}/public/Yvonne-discord-pdp.png"

        if file_bytes:
            # Send as Multipart Form Attachment
            resp = requests.post(
                target_url,
                data={"username": "Yvonne", "avatar_url": avatar_url},
                files={"file": (filename + ".mp4", file_bytes, "video/mp4")}
            )
        else:
            # Fallback to Text URL
            payload = {
                "content": public_mp4_url,
                "username": "Yvonne",
                "avatar_url": avatar_url
            }
            resp = requests.post(target_url, json=payload)
        
        if resp.status_code in [200, 204]:
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"error": f"Discord Error: {resp.status_code} {resp.text}"}), 500
            
    except Exception as e:
        print(f"Publish error: {e}")
        return jsonify({"error": str(e)}), 500

def get_all_badge_rules():
    if not supabase: return []
    try:
        res = supabase.table('badge_rules').select('*').execute()
        return res.data
    except: return []

def get_user_data(user_id):
    if not supabase: return {}
    try:
        res = supabase.table('users').select('*').eq('id', user_id).execute()
        if res.data: return res.data[0]
        return {}
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return {}

def update_user_stat(user_id, stat, delta=1):
    """Updates a stat (uploads/votes) and checks for badge awards dynamically."""
    if not supabase: return []
    try:
        res = supabase.table('users').select('*').eq('id', user_id).execute()
        user_data = res.data[0] if res.data else {"id": str(user_id), "uploads": 0, "votes": 0, "badges": []}
            
        user_data[stat] = user_data.get(stat, 0) + delta
        my_badges = user_data.get("badges", [])
        new_badges = []
        
        all_rules = get_all_badge_rules()
        for rule in all_rules:
            bid = rule["id"]
            if bid in my_badges: continue
            
            ctype = rule.get("condition_type")
            cval = rule.get("condition_value", 0)
            
            if ctype == "upload" and stat == "uploads" and user_data["uploads"] >= cval:
                my_badges.append(bid)
                new_badges.append(rule)
            elif ctype == "vote" and stat == "votes" and user_data["votes"] >= cval:
                my_badges.append(bid)
                new_badges.append(rule)

        if not res.data:
            supabase.table('users').insert({**user_data, stat: user_data[stat], "badges": my_badges}).execute()
        else:
            supabase.table('users').update({stat: user_data[stat], "badges": my_badges}).eq('id', user_id).execute()
        
        return new_badges
    except Exception as e:
        print(f"Update user stat error: {e}")
        return []

@app.route('/api/user/<user_id>')
def get_user_profile(user_id):
    """Returns profile info + fetches Discord Avatar."""
    data = get_user_data(user_id)
    all_rules_dict = {r["id"]: r for r in get_all_badge_rules()}
    
    enriched_badges = []
    for bid in data.get("badges", []):
         if bid in all_rules_dict: enriched_badges.append(all_rules_dict[bid])
    
    avatar_url = None
    username = "UNKNOWN"
    is_bot = False
    
    try:
        import requests
        headers = { "Authorization": f"Bot {os.getenv('DISCORD_BOT_TOKEN')}" }
        r = requests.get(f"https://discord.com/api/v10/users/{user_id}", headers=headers)
        if r.status_code == 200:
            u = r.json()
            username = u.get('global_name') or u.get('username', "UNKNOWN")
            is_bot = u.get('bot', False)
            if u.get('avatar'):
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{u['avatar']}.png"
            else:
                discriminator = int(u.get('discriminator', 0))
                avatar_url = f"https://cdn.discordapp.com/embed/avatars/{discriminator % 5}.png"
    except Exception as e:
        print(f"Avatar fetch error: {e}")

    return jsonify({
        "id": user_id,
        "username": username,
        "is_bot": is_bot,
        "avatar_url": avatar_url,
        "description": data.get("description", "No Data Available."),
        "stats": {
            "uploads": data.get("uploads", 0),
            "votes": data.get("votes", 0)
        },
        "badges": enriched_badges,
        "is_admin": is_admin_user(user_id),
        "is_mod": is_mod_user(user_id)
    })


@app.route('/api/badges/create', methods=['POST'])
def create_badge():
    user_id = request.json.get('user_id')
    if not can_manage(user_id): return jsonify({"error": "Admin only"}), 403
    
    badge_data = request.json.get('badge')
    bid = badge_data.get('id')
    
    DEFAULT_BADGES[bid] = badge_data
    return jsonify({"status": "created (in-memory)"})


@app.route('/api/user/update', methods=['POST'])
def update_user_profile():
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    data = request.json
    user_id = data.get('user_id')
    desc = data.get('description')
    
    if desc is not None:
        try:
            res = supabase.table('users').select('*').eq('id', user_id).execute()
            if not res.data:
                supabase.table('users').insert({"id": user_id, "description": desc[:500]}).execute()
            else:
                supabase.table('users').update({'description': desc[:500]}).eq('id', user_id).execute()
        except Exception as e:
            print(f"Error updating profile: {e}")
            return jsonify({"error": str(e)}), 500
        
    return jsonify({"status": "ok"})

@app.route('/api/members', methods=['GET'])
def get_guild_members():
    guild_id = request.args.get('guild_id')
    if not guild_id: return jsonify({"error": "Missing guild_id"}), 400
    
    try:
        url = f"https://discord.com/api/v10/guilds/{guild_id}/members?limit=100"
        import requests
        r = requests.get(url, headers=get_discord_headers())
        
        if r.status_code != 200:
            return jsonify({"error": f"Discord API Error: {r.status_code}"}), r.status_code
            
        members_data = r.json()
        
        db_users = {}
        if supabase:
            u_res = supabase.table('users').select('*').execute()
            for row in u_res.data:
                db_users[row['id']] = row
        
        parsed_members = []
        for m in members_data:
            u = m['user']
            uid = u['id']
            is_bot = u.get('bot', False)
            
            db_u = db_users.get(uid, {"uploads":0, "votes":0})
            stats = {"uploads": db_u.get("uploads", 0), "votes": db_u.get("votes", 0)}
            
            parsed_members.append({
                "id": uid,
                "username": u['username'],
                "global_name": u.get('global_name', u['username']),
                "avatar": f"https://cdn.discordapp.com/avatars/{uid}/{u['avatar']}.png" if u.get('avatar') else None,
                "is_bot": is_bot,
                "is_admin": is_admin_user(uid),
                "is_mod": is_mod_user(uid),
                "stats": stats
            })
            
        return jsonify(parsed_members)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- BADGE MANAGER ENDPOINTS ---
@app.route('/api/badges/rules', methods=['GET', 'POST', 'DELETE'])
def manage_badge_rules():
    if not supabase: return jsonify({"error": "No DB connection"}), 500
    
    if request.method == 'GET':
        return jsonify(get_all_badge_rules())
        
    data = request.json
    user_id = data.get('user_id')
    if not can_manage(user_id):
        return jsonify({"error": "Admin clearance required"}), 403
        
    if request.method == 'POST':
        try:
            new_rule = {
                "name": data.get("name"),
                "icon": data.get("icon"),
                "condition_type": data.get("condition_type"),
                "condition_value": int(data.get("condition_value", 0)),
                "show_on_card": data.get("show_on_card", False)
            }
            res = supabase.table('badge_rules').insert(new_rule).execute()
            return jsonify({"status": "ok", "rule": res.data[0]})
        except Exception as e:
            return jsonify({"error": str(e)}), 400
            
    if request.method == 'DELETE':
        rule_id = data.get("rule_id")
        try:
            supabase.table('badge_rules').delete().eq('id', rule_id).execute()
            return jsonify({"status": "deleted"})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# --- EXISTING ENDPOINTS UPDATES ---

@app.route('/api/favorites', methods=['GET', 'POST'])
def favorites():
    """Handles User Favorites via Supabase."""
    if not supabase: return jsonify({"favorites": []})
        
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id: return jsonify({"favorites": []})
        try:
            res = supabase.table('favorites').select('filename').eq('user_id', user_id).execute()
            user_favs = [row['filename'] for row in res.data]
            return jsonify({"favorites": user_favs})
        except:
            return jsonify({"favorites": []})
        
    if request.method == 'POST':
        data = request.json
        user_id = data.get('user_id')
        filename = data.get('filename')
        action = data.get('action')
        
        if not user_id or not filename: return jsonify({"error": "Missing data"}), 400
        
        try:
            if action == 'add':
                supabase.table('favorites').upsert({"user_id": user_id, "filename": filename}).execute()
            elif action == 'remove':
                supabase.table('favorites').delete().eq('user_id', user_id).eq('filename', filename).execute()
                
            res = supabase.table('favorites').select('filename').eq('user_id', user_id).execute()
            user_favs = [row['filename'] for row in res.data]
            return jsonify({"status": "ok", "favorites": user_favs})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def convert_file():
    if 'files' not in request.files: return jsonify({"error": "No files"}), 400
    files = request.files.getlist('files')
    if not files: return jsonify({"error": "Empty file list"}), 400
    
    task_id = request.form.get('task_id', 'unknown')
    auto_upload = request.form.get('auto_upload') == 'true'
    user_id = request.form.get('user_id')
    
    start_time = request.form.get('start_time')
    if start_time: start_time = float(start_time)
    end_time = request.form.get('end_time')
    if end_time: end_time = float(end_time)

    if auto_upload and not can_manage(user_id):
         return jsonify({"error": "Unauthorized to auto-upload"}), 403
    
    import zipfile
    import uuid
    import shutil
    
    batch_id = str(uuid.uuid4())[:8]
    cache_dir = os.path.join(BASE_DIR, '.cache', f'batch_{batch_id}')
    os.makedirs(cache_dir, exist_ok=True)
    
    converted_files = []
    
    for file in files:
        if file.filename == '': continue
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.mp4', '.mpgif', '.gif']: continue
        target_ext = '.mpgif' if ext in ['.mp4', '.mov', '.webm', '.gif'] else '.mp4'
        base_name = secure_filename(os.path.splitext(file.filename)[0] + target_ext)
        
        # We need a source path for the web upload
        src_path = os.path.join(cache_dir, f"raw_{file.filename}")
        out_path = os.path.join(cache_dir, base_name)
        
        file.save(src_path)
        
        def cb(saved, total, elapsed, eta):
            percent = int((saved / total) * 100) if total > 0 else 0
            percent = max(0, min(100, percent))
            progress_tracker[task_id] = {
                "status": "converting", 
                "percent": percent, 
                "current_file": base_name
            }

        # ACTUALLY execute the conversion!
        try:
            from convertisseur.converter import video_to_mpgif
            progress_tracker[task_id] = {"status": "converting", "percent": 0, "current_file": base_name}
            video_to_mpgif(src_path, out_path, preset="balanced", progress_callback=cb, start_time=start_time, end_time=end_time)
            
            if auto_upload:
                try:
                    process_mpgif_upload(out_path, base_name, user_id)
                except Exception as ue:
                    print(f"Auto-upload failed for {base_name}: {ue}")
            
            converted_files.append(base_name)
        except Exception as e:
            print(f"Failed to convert {file.filename}: {e}")
        finally:
            if os.path.exists(src_path):
                os.remove(src_path)
            if auto_upload and os.path.exists(out_path):
                try: os.remove(out_path)
                except: pass
        
    if not converted_files:
        return jsonify({"error": "No valid files converted"}), 400
        
    if auto_upload:
        # Don't generate zip, just return ok
        return jsonify({"status": "ok", "auto_uploaded": True}), 200

    zip_filename = f"Endfield_Conversion_{batch_id}.zip"
    zip_path = os.path.join(BASE_DIR, '.cache', zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in converted_files:
            zipf.write(os.path.join(cache_dir, f), f)
            
    return jsonify({
        "status": "success",
        "batch_id": batch_id,
        "files": converted_files,
        "zip_url": f"/api/download_zip/{batch_id}"
    })

@app.route('/api/download_zip/<batch_id>', methods=['GET'])
def download_zip(batch_id):
    zip_path = os.path.join(BASE_DIR, '.cache', f"Endfield_Conversion_{batch_id}.zip")
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    return "Not Found", 404

@app.route('/api/download_converted/<batch_id>/<filename>', methods=['GET'])
def download_converted(batch_id, filename):
    file_path = os.path.join(BASE_DIR, '.cache', f'batch_{batch_id}', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "Not Found", 404

@app.route('/favicon.ico')
def favicon():
    return "", 204

# ___ SERVER RUN ___
@app.route('/api/upscale_avatar', methods=['POST'])
def upscale_avatar():
    try:
        data = request.json
        user_id = data.get('user_id')
        avatar_url = data.get('avatar_url')
        model = data.get('model', 'waifu2x')
        scale = data.get('scale', 2)
        
        if not user_id or not avatar_url:
            return jsonify({"error": "Missing parameters"}), 400
            
        sys.path.append(os.path.dirname(BASE_DIR))
        import upscaler
        
        b64_img = upscaler.upscale_image_base64(avatar_url, model, scale)
        return jsonify({"success": True, "image_b64": b64_img})
        
    except Exception as e:
        print(f"Upscale API error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print(" * \033[93mTips: Install 'python-dotenv' to load variables from .env file.\033[0m")

    try:
        from pyngrok import ngrok, conf
        
        ngrok_token = os.getenv("NGROK_AUTHTOKEN")
        if ngrok_token:
            conf.get_default().auth_token = ngrok_token
            print(" * \033[92mNgrok Auth Token loaded from environment.\033[0m")
        
        public_url = ngrok.connect(5000).public_url
        os.environ["SERVER_URL"] = public_url
        print(f" * \033[92mngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:5000\"\033[0m")
        print(f" * Update SERVER_URL in .env or bot.py to: {public_url}")
        
    except ImportError:
        print(" * \033[93mTips: Install 'pyngrok' (pip install pyngrok) to auto-generate a public URL.\033[0m")
    except Exception as e:
        if "ERR_NGROK_4018" in str(e):
            print("\n\033[91m❌ NGROK AUTH REQUIRED\033[0m")
            print("To use ngrok, you need a free account.")
            print("1. Go to: https://dashboard.ngrok.com/signup")
            print("2. Copy your Authtoken")
            print("3. Run: \033[96mngrok config add-authtoken YOUR_TOKEN\033[0m")
            print("   (Or ensure 'ngrok' is in your PATH and run command manually)\n")
        else:
            print(f" * ngrok error: {e}")

    app.run(host='0.0.0.0', port=5000)
