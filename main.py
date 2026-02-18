import argparse
import sys
import tkinter.messagebox
import tkinter
from convertisseur.converter import video_to_mpgif, mpgif_to_video
from lecteur.player import MPGIFPlayer
from lecteur.gui import MPGIFGui

class NullWriter:
    def write(self, data): pass
    def flush(self): pass

if sys.stdout is None: sys.stdout = NullWriter()
if sys.stderr is None: sys.stderr = NullWriter()

def main():
    if len(sys.argv) < 2:
        try:
            gui = MPGIFGui()
            gui.run()
            return
        except Exception as e:
            root = tkinter.Tk()
            root.withdraw()
            tkinter.messagebox.showerror("Fatal Error", f"Impossible to launch the GUI:\n{e}")
            return

    parser = argparse.ArgumentParser(description="MPGIF Tool: Encode, Decode, and Play .mpgif files.")
    subparsers = parser.add_subparsers(dest="command")

    # ENCODE
    encode_parser = subparsers.add_parser("encode", help="Convert video to .mpgif", 
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    encode_parser.add_argument("input", help="Input video file or Directory")
    encode_parser.add_argument("output", help="Output .mpgif file or Directory", nargs='?')
    encode_parser.add_argument("--preset", choices=["gif-like", "balanced", "hq", "archival"], help="Use a compression preset (overrides other settings)")
    encode_parser.add_argument("--width", type=int, default=480, help="Target width (height auto-calculated)")
    encode_parser.add_argument("--fps", type=int, default=15, help="Target FPS")
    encode_parser.add_argument("--quality", type=int, default=75, help="WebP quality (0-100)")
    encode_parser.add_argument("--loop", type=int, default=0, help="Loop count (0 for infinite)")
    encode_parser.add_argument("--title", help="Metadata: Title")
    encode_parser.add_argument("--author", help="Metadata: Author")
    encode_parser.add_argument("--tags", help="Metadata: Tags (comma separated)")

    # DECODE
    decode_parser = subparsers.add_parser("decode", help="Convert .mpgif to video",
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    decode_parser.add_argument("input", help="Input .mpgif file or Directory")
    decode_parser.add_argument("output", help="Output video file or Directory", nargs='?')

    # PLAY
    play_parser = subparsers.add_parser("play", help="Play .mpgif file from CLI",
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    play_parser.add_argument("input", nargs='?', help="Input .mpgif file (optional, opens picker if empty)")

    ui_parser = subparsers.add_parser("gui", help="Open Desktop GUI Launcher",
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    args = parser.parse_args()

    if args.command == "encode":
        import os
        import time
        
        metadata = {}
        if args.title: metadata['title'] = args.title
        if args.author: metadata['author'] = args.author
        if args.tags: metadata['tags'] = args.tags
        metadata['timestamp'] = time.ctime()

        if os.path.isdir(args.input):
            # BATCH MODE
            if not args.output: args.output = args.input
            if not os.path.isdir(args.output): os.makedirs(args.output, exist_ok=True)
            
            files = [f for f in os.listdir(args.input) if f.lower().endswith(('.mp4', '.webm', '.gif', '.mov'))]
            print(f"📦 Batch Encoding: {len(files)} files found in {args.input}")
            
            for f in files:
                in_path = os.path.join(args.input, f)
                out_name = os.path.splitext(f)[0] + ".mpgif"
                out_path = os.path.join(args.output, out_name)
                print(f"  > Processing {f}...")
                try:
                    video_to_mpgif(in_path, out_path, preset=args.preset, 
                                   target_fps=args.fps, width=args.width, 
                                   quality=args.quality, loop=args.loop, metadata=metadata)
                except Exception as e:
                    print(f"  ❌ Error: {e}")
        else:
            # SINGLE MODE
            if not args.output: args.output = os.path.splitext(args.input)[0] + ".mpgif"
            print(f"🎬 Encoding : {args.input} -> {args.output}")
            video_to_mpgif(args.input, args.output, preset=args.preset, 
                           target_fps=args.fps, width=args.width, 
                           quality=args.quality, loop=args.loop, metadata=metadata)
    
    elif args.command == "decode":
        import os
        if os.path.isdir(args.input):
            # BATCH MODE
            if not args.output: args.output = args.input
            if not os.path.isdir(args.output): os.makedirs(args.output, exist_ok=True)
            
            files = [f for f in os.listdir(args.input) if f.lower().endswith('.mpgif')]
            print(f"📦 Batch Decoding: {len(files)} files found in {args.input}")
            
            for f in files:
                in_path = os.path.join(args.input, f)
                out_name = os.path.splitext(f)[0] + ".mp4"
                out_path = os.path.join(args.output, out_name)
                print(f"  > Processing {f}...")
                try:
                    mpgif_to_video(in_path, out_path)
                except Exception as e:
                    print(f"  ❌ Error: {e}")
        else:
            # SINGLE MODE
            if not args.output: args.output = os.path.splitext(args.input)[0] + ".mp4"
            print(f"🎞️ Decoding : {args.input} -> {args.output}")
            mpgif_to_video(args.input, args.output)

    elif args.command == "play":
        print(f"▶️ Reading...")
        player = MPGIFPlayer(args.input)
        player.run()

    elif args.command == "gui":
        print("🖥️ GUI Launching...")
        gui = MPGIFGui()
        gui.run()

if __name__ == "__main__":
    main()
