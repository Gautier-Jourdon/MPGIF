import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import threading
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lecteur.player import MPGIFPlayer
from convertisseur.converter import video_to_mpgif, mpgif_to_video

BG_COLOR = "#1e1e1e"
FG_COLOR = "#ffffff"
ACCENT_COLOR = "#ff9800"
ACCENT_HOVER = "#e68900"
SECONDARY_BG = "#2d2d2d"

class MPGIFGui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MPGIF Studio")
        self.root.geometry("600x450")
        self.root.configure(bg=BG_COLOR)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure(".", background=BG_COLOR, foreground=FG_COLOR, fieldbackground=SECONDARY_BG)
        self.style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 10))
        self.style.configure("TButton", background=ACCENT_COLOR, foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0)
        self.style.map("TButton", background=[('active', ACCENT_HOVER)])
        self.style.configure("TEntry", fieldbackground=SECONDARY_BG, foreground=FG_COLOR, insertcolor=FG_COLOR)
        self.style.configure("TNotebook", background=BG_COLOR, tabposition='n')
        self.style.configure("TNotebook.Tab", background=SECONDARY_BG, foreground=FG_COLOR, padding=[10, 5], font=("Segoe UI", 10))
        self.style.map("TNotebook.Tab", background=[('selected', ACCENT_COLOR)], foreground=[('selected', 'white')])

        title_font = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        header = tk.Label(self.root, text="MPGIF Studio", bg=BG_COLOR, fg=ACCENT_COLOR, font=title_font)
        header.pack(pady=15)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=20, pady=10)

        self.tab_encode = tk.Frame(self.notebook, bg=BG_COLOR)
        self.tab_decode = tk.Frame(self.notebook, bg=BG_COLOR)
        self.tab_play = tk.Frame(self.notebook, bg=BG_COLOR)

        self.notebook.add(self.tab_encode, text=" Créer (.mpgif) ")
        self.notebook.add(self.tab_decode, text=" Extraire (.mp4) ")
        self.notebook.add(self.tab_play, text=" Lecture ")

        self.setup_encode_tab()
        self.setup_decode_tab()
        self.setup_play_tab()
        
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bg=BG_COLOR, fg="#888888", font=("Segoe UI", 9))
        self.status_bar.pack(side="bottom", fill="x", pady=5)


    def setup_encode_tab(self):
        frame = self.tab_encode
        
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Vidéo source :", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.enc_input = ttk.Entry(frame)
        self.enc_input.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="...", width=3, command=lambda: self.browse_file(self.enc_input, filetype="video")).grid(row=0, column=2, padx=10)

        tk.Label(frame, text="Dossier destination :", bg=BG_COLOR, fg=FG_COLOR).grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.enc_output = ttk.Entry(frame)
        self.enc_output.grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="...", width=3, command=lambda: self.choose_directory(self.enc_output)).grid(row=1, column=2, padx=10)

        opts_frame = tk.Frame(frame, bg=BG_COLOR)
        opts_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="w", padx=10)
        
        tk.Label(opts_frame, text="Largeur:", bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=5)
        self.enc_width = ttk.Entry(opts_frame, width=6)
        self.enc_width.insert(0, "480")
        self.enc_width.pack(side="left")

        tk.Label(opts_frame, text="FPS:", bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=5)
        self.enc_fps = ttk.Entry(opts_frame, width=5)
        self.enc_fps.insert(0, "15")
        self.enc_fps.pack(side="left")

        tk.Label(opts_frame, text="Qualité:", bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=5)
        self.enc_qual = ttk.Entry(opts_frame, width=5)
        self.enc_qual.insert(0, "75")
        self.enc_qual.pack(side="left")

        tk.Label(opts_frame, text="Boucle (0=inf):", bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=5)
        self.enc_loop = ttk.Entry(opts_frame, width=5)
        self.enc_loop.insert(0, "0")
        self.enc_loop.pack(side="left")

        ttk.Button(frame, text="CONVERTIR EN .MPGIF", command=self.run_encode).grid(row=3, column=0, columnspan=3, pady=20, sticky="ew", padx=50)


    def setup_decode_tab(self):
        frame = self.tab_decode
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Fichier .mpgif :", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.dec_input = ttk.Entry(frame)
        self.dec_input.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="...", width=3, command=lambda: self.browse_file(self.dec_input, filetype="mpgif")).grid(row=0, column=2, padx=10)

        tk.Label(frame, text="Dossier destination :", bg=BG_COLOR, fg=FG_COLOR).grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.dec_output = ttk.Entry(frame)
        self.dec_output.grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="...", width=3, command=lambda: self.choose_directory(self.dec_output)).grid(row=1, column=2, padx=10)

        ttk.Button(frame, text="EXTRAIRE EN .MP4", command=self.run_decode).grid(row=2, column=0, columnspan=3, pady=20, sticky="ew", padx=50)


    def setup_play_tab(self):
        frame = self.tab_play
        
        info_lbl = tk.Label(frame, text="Le lecteur s'ouvrira dans une nouvelle fenêtre.", bg=BG_COLOR, fg="#aaaaaa", font=("Segoe UI", 11, "italic"))
        info_lbl.pack(pady=40)

        ttk.Button(frame, text="OUVRIR UN FICHIER", command=self.run_player).pack(ipadx=20, ipady=10)


    def browse_file(self, entry_widget, filetype="all"):
        types = [("Tous les fichiers", "*.*")]
        if filetype == "mpgif":
            types = [("Fichier MPGIF", "*.mpgif"), ("Tous les fichiers", "*.*")]
        elif filetype == "video":
            types = [("Vidéos", "*.mp4 *.webm *.gif *.avi *.mov"), ("Tous les fichiers", "*.*")]
            
        filename = filedialog.askopenfilename(filetypes=types)
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def choose_directory(self, entry_widget):
        directory = filedialog.askdirectory()
        if directory:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, directory)

    def set_status(self, msg, color=FG_COLOR):
        self.status_var.set(msg)
        self.status_bar.config(fg=color)
        self.root.update_idletasks()


    def run_encode(self):
        inp = self.enc_input.get()
        out = self.enc_output.get()
        
        if not inp or not out:
            messagebox.showwarning("Erreur", "Veuillez sélectionner les fichiers source et le dossier de destination.")
            return

        if not os.path.isdir(out):
             messagebox.showwarning("Erreur", "Le chemin de destination n'est pas un dossier valide.")
             return
             
        filename = os.path.splitext(os.path.basename(inp))[0] + ".mpgif"
        output_path = os.path.join(out, filename)

        try:
            fps = int(self.enc_fps.get())
            width = int(self.enc_width.get())
            quality = int(self.enc_qual.get())
            loop = int(self.enc_loop.get())
        except ValueError:
             messagebox.showwarning("Erreur", "Veuillez entrer des nombres valides pour les options.")
             return

        self.set_status(f"⏳ Encodage en cours... ({os.path.basename(inp)})", ACCENT_COLOR)
        
        def update_progress(current, total, elapsed, eta):
            pct = int((current / total) * 100)
            elapsed_str = f"{int(elapsed)}s"
            eta_str = f"{int(eta)}s"
            self.root.after(0, lambda: self.set_status(f"⏳ Encodage: {pct}% | Temps: {elapsed_str} | Restant: {eta_str}", ACCENT_COLOR))

        def encoding_task():
            try:
                video_to_mpgif(inp, output_path, target_fps=fps, width=width, quality=quality, loop=loop, progress_callback=update_progress)
                self.root.after(0, lambda: self.set_status("✅ Encodage terminé avec succès !", "#00ff00"))
                self.root.after(0, lambda: messagebox.showinfo("Succès", f"Fichier créé : {output_path}"))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda: self.set_status(f"❌ Erreur: {err_msg}", "#ff0000"))
                self.root.after(0, lambda: messagebox.showerror("Erreur", err_msg))

        threading.Thread(target=encoding_task, daemon=True).start()

    def run_decode(self):
        inp = self.dec_input.get()
        out = self.dec_output.get()
        
        if not inp or not out:
            messagebox.showwarning("Erreur", "Veuillez sélectionner les fichiers source et le dossier de destination.")
            return

        if not os.path.isdir(out):
             messagebox.showwarning("Erreur", "Le chemin de destination n'est pas un dossier valide.")
             return

        filename = os.path.splitext(os.path.basename(inp))[0] + ".mp4"
        output_path = os.path.join(out, filename)

        self.set_status(f"⏳ Extraction en cours... ({os.path.basename(inp)})", ACCENT_COLOR)
        
        def decoding_task():
            try:
                mpgif_to_video(inp, output_path)
                self.root.after(0, lambda: self.set_status("✅ Extraction terminée avec succès !", "#00ff00"))
                self.root.after(0, lambda: messagebox.showinfo("Succès", f"Fichier extrait : {output_path}"))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda: self.set_status(f"❌ Erreur: {err_msg}", "#ff0000"))
                self.root.after(0, lambda: messagebox.showerror("Erreur", err_msg))

        threading.Thread(target=decoding_task, daemon=True).start()

    def run_player(self):
        self.root.withdraw()
        
        filename = filedialog.askopenfilename(title="Lire un fichier .mpgif", filetypes=[("Fichiers MPGIF", "*.mpgif")])
        if filename:
            self.set_status(f"▶️ Lecture de {os.path.basename(filename)}...")
            try:
                player = MPGIFPlayer(filename)
                player.run()
                self.set_status("Prêt")
                self.root.deiconify()
            except Exception as e:
                self.set_status(f"❌ Erreur lecture: {e}", "#ff0000")
        else:
             self.root.deiconify()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = MPGIFGui()
    gui.run()
