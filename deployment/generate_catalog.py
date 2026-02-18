import os
import base64

def generate_catalog(directory="."):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_dir = os.path.join(base_dir, "web")
    
    # Read Template
    with open(os.path.join(web_dir, "index.html"), "r", encoding="utf-8") as f:
        html_template = f.read()

    # Read JS
    with open(os.path.join(web_dir, "mpgif_reader.js"), "r", encoding="utf-8") as f:
        js_content = f.read()

    # Embed JS
    html_out = html_template.replace('<script src="mpgif_reader.js"></script>', f'<script>{js_content}</script>')
    
    # Inject Loader Script
    loader_script = """
    <script>
        // Auto-load files from directory (Simulated via File Loading logic in static build)
        // In a real static local context properly we can't list files easily without a server.
        // So we will modify the page to be a "Drag & Drop Viewer" primarily, 
        // OR we can embed base64 data if files are small (not recommended for video).
        
        // For this local tool, we will just ensure the viewer is ready.
        document.addEventListener('DOMContentLoaded', () => {
             console.log("Catalog ready. Drag and drop .mpgif files to view.");
        });
    </script>
    """
    
    # Actually, to make it a "Catalog", we should ideally scan files and create a JSON index if served via HTTP.
    # But since this is a local file opener, we'll keep the Drag & Drop focus as the "Viewer"
    # and maybe list files if we were running a python server.
    
    # Let's create a specialized "server" version or just a static viewer.
    # The user asked for "Local Catalog - Petit dossier indexé".
    # The best way without a server is to generate an HTML that *references* relative files.
    # But JS can't read local files via fetch() easily due to CORS if double-clicked.
    
    # hybrid approach: references files assuming Firefox/relaxed browser or python server.
    
    mpgif_files = [f for f in os.listdir(directory) if f.lower().endswith('.mpgif')]
    
    js_file_list = "const localFiles = " + str(mpgif_files) + ";"
    
    injector = f"""
    <script>
        {js_file_list}
        
        // Try to load local files via fetch (Requires local server like 'python -m http.server')
        async function loadLocalCatalog() {{
            if (localFiles.length > 0) {{
                document.getElementById('drop-zone').style.display = 'none';
                document.getElementById('gallery').style.display = 'grid';
                
                for (const filename of localFiles) {{
                    try {{
                        const resp = await fetch(filename);
                        if (!resp.ok) continue;
                        const blob = await resp.blob();
                        const file = new File([blob], filename);
                        loadMPGIF(file);
                    }} catch (e) {{
                        console.warn("Could not auto-load (CORS?):", filename);
                    }}
                }}
            }}
        }}
        
        loadLocalCatalog();
    </script>
    """

    html_out = html_out.replace('</body>', f'{injector}</body>')

    out_file = os.path.join(directory, "catalog.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_out)
    
    print(f"✅ Catalog generated: {out_file}")
    print(f"ℹ️  To view, run 'python -m http.server' in this directory and open http://localhost:8000/catalog.html")

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    generate_catalog(target)
