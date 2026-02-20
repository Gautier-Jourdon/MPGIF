import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Cannot migrate: Missing Supabase credentials in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"🔗 Connected to {SUPABASE_URL}")
print("🚀 Beginning Data Migration to Supabase...")

# 1. Migrate Users
users_file = os.path.join(BASE_DIR, 'users.json')
if os.path.exists(users_file):
    with open(users_file, 'r', encoding='utf-8') as f:
        users = json.load(f)
        count = 0
        for uid, data in users.items():
            supabase.table('users').upsert({
                "id": uid,
                "uploads": data.get('uploads', 0),
                "votes": data.get('votes', 0),
                "badges": data.get('badges', []),
                "description": data.get('description', '')
            }).execute()
            count += 1
    print(f"✅ Migrated {count} users from users.json")

# 2. Migrate Metadata to files
meta_file = os.path.join(BASE_DIR, 'metadata.json')
if os.path.exists(meta_file):
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)
        count = 0
        for fname, data in meta.items():
            supabase.table('files').upsert({
                "filename": fname,
                "custom_name": data.get('custom_name'),
                "width": data.get('width', 0),
                "height": data.get('height', 0),
                "uploader_id": data.get('uploader_id') # If available in your old json
            }).execute()
            count += 1
    print(f"✅ Migrated {count} files from metadata.json")

# 3. Migrate Votes
votes_file = os.path.join(BASE_DIR, 'votes.json')
if os.path.exists(votes_file):
    with open(votes_file, 'r', encoding='utf-8') as f:
        votes = json.load(f)
        count = 0
        for fname, file_votes in votes.items():
            for uid in file_votes.get('up', []):
                supabase.table('votes').upsert({"filename": fname, "user_id": uid, "vote_type": "up"}).execute()
                count += 1
            for uid in file_votes.get('down', []):
                supabase.table('votes').upsert({"filename": fname, "user_id": uid, "vote_type": "down"}).execute()
                count += 1
    print(f"✅ Migrated {count} votes from votes.json")

# 4. Migrate Favorites
fav_file = os.path.join(BASE_DIR, 'favorites.json')
if os.path.exists(fav_file):
    with open(fav_file, 'r', encoding='utf-8') as f:
        favs = json.load(f)
        count = 0
        for uid, files in favs.items():
            for fname in files:
                supabase.table('favorites').upsert({"filename": fname, "user_id": uid}).execute()
                count += 1
    print(f"✅ Migrated {count} favorites from favorites.json")

print("\n🎉 Migration of JSON databases complete.")
print("ℹ️ Note: This script ONLY migrates Postgres data. You must manually upload your `mpgifs` and `.cache` files to the Supabase Storage Bucket if you want to preserve the actual media files, or wipe them and start fresh.")
