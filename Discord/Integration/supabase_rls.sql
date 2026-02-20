-- Security Policy definitions for Supabase

-- Since the Python backend connects using the SUPABASE_KEY (which should be the Service Role Key
-- configured in your .env) or acts as an admin layer that checks Discord user authentication,
-- we simply enable RLS and allow public read access where necessary, while letting the backend 
-- handle all the inserts/deletes bypassing RLS constraints automatically.

-- Enable Row Level Security
ALTER TABLE "public"."users" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."files" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."votes" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."favorites" ENABLE ROW LEVEL SECURITY;

-- 1. USERS: Anyone can read user stats/badges. (Needed for profile pages)
CREATE POLICY "Public Read Users" ON "public"."users" 
FOR SELECT USING (true);

-- 2. FILES: Anyone can view the file catalog and metadata.
CREATE POLICY "Public Read Files" ON "public"."files" 
FOR SELECT USING (true);

-- 3. VOTES: Anyone can view vote counts
CREATE POLICY "Public Read Votes" ON "public"."votes" 
FOR SELECT USING (true);

-- 4. FAVORITES: Anyone can view favorites
CREATE POLICY "Public Read Favorites" ON "public"."favorites" 
FOR SELECT USING (true);

-- Note: No INSERT/UPDATE/DELETE policies are created for the `anon` role here.
-- This ensures that only the authenticated Backend Server can modify data.
-- The server code explicitly handles Discord user authorization.

-- -- STORAGE BUCKETS -- --
-- Remember to navigate to Storage > Policies in your Supabase dashboard.
-- 1. Create a public SELECT policy on the "mpgifs" bucket so users can load images and videos directly using the public URL.
-- 2. Do not create public INSERT policies; the python backend handles the uploads.
