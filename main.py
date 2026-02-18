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

    encode_parser = subparsers.add_parser("encode", help="Convert video to .mpgif", 
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    encode_parser.add_argument("input", help="Input video file (MP4, WEBM, GIF, etc.)")
    encode_parser.add_argument("output", help="Output .mpgif file")
    encode_parser.add_argument("--width", type=int, default=480, help="Target width (height auto-calculated)")
    encode_parser.add_argument("--fps", type=int, default=15, help="Target FPS")
    encode_parser.add_argument("--quality", type=int, default=75, help="WebP quality (0-100)")
    encode_parser.add_argument("--loop", type=int, default=0, help="Loop count (0 for infinite)")

    decode_parser = subparsers.add_parser("decode", help="Convert .mpgif to video",
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    decode_parser.add_argument("input", help="Input .mpgif file")
    decode_parser.add_argument("output", help="Output video file (MP4)")

    play_parser = subparsers.add_parser("play", help="Play .mpgif file from CLI",
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    play_parser.add_argument("input", nargs='?', help="Input .mpgif file (optional, opens picker if empty)")

    ui_parser = subparsers.add_parser("gui", help="Open Desktop GUI Launcher",
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    args = parser.parse_args()

    if args.command == "encode":
        print(f"🎬 Encoding : {args.input} -> {args.output}")
        video_to_mpgif(args.input, args.output, 
                       target_fps=args.fps, 
                       width=args.width, 
                       quality=args.quality, 
                       loop=args.loop)
    
    elif args.command == "decode":
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
