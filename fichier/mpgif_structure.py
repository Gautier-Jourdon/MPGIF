import struct
import os
import json

SIGNATURE = b'MPGIF'
VERSION_1 = 1
VERSION_2 = 2
CURRENT_VERSION = VERSION_2

HEADER_FORMAT = '>5sBHHBIB'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
FRAME_HEADER_FORMAT = '>I'
AUDIO_HEADER_FORMAT = '>BI'

CODEC_OPUS = 1
CODEC_AAC = 2
CODEC_MP3 = 3

class MPGIFWriter:
    def __init__(self, filename, width, height, fps, loop_count=0):
        self.filename = filename
        self.width = width
        self.height = height
        self.fps = fps
        self.loop_count = loop_count
        self.frames = []
        self.audio_data = None
        self.audio_codec = CODEC_OPUS
        self.metadata = {}  # Metadata dictionary (Author, Timestamp, etc.)

    def add_frame(self, frame_data):
        """Adds a compressed frame (bytes) to the list."""
        self.frames.append(frame_data)

    def set_audio(self, audio_data, codec=CODEC_OPUS):
        """Sets the compressed audio data."""
        self.audio_data = audio_data
        self.audio_codec = codec

    def set_metadata(self, key, value):
        self.metadata[key] = value

    def write(self):
        """Writes the .mpgif file (Version 2 with Metadata)."""
        with open(self.filename, 'wb') as f:
            # Header
            header = struct.pack(
                HEADER_FORMAT,
                SIGNATURE,
                CURRENT_VERSION,
                self.width,
                self.height,
                self.fps,
                len(self.frames),
                self.loop_count
            )
            f.write(header)

            # Frames
            for frame in self.frames:
                f.write(struct.pack(FRAME_HEADER_FORMAT, len(frame)))
                f.write(frame)

            # Audio
            if self.audio_data:
                f.write(struct.pack(AUDIO_HEADER_FORMAT, self.audio_codec, len(self.audio_data)))
                f.write(self.audio_data)
            else:
                f.write(struct.pack(AUDIO_HEADER_FORMAT, 0, 0))

            # Metadata (Version 2+)
            if self.metadata:
                meta_json = json.dumps(self.metadata).encode('utf-8')
                f.write(struct.pack('>I', len(meta_json)))
                f.write(meta_json)
            else:
                f.write(struct.pack('>I', 0)) # No metadata
        
        print(f"✅ Fichier {self.filename} écrit avec succès (v{CURRENT_VERSION}).")

class MPGIFReader:
    def __init__(self, filename):
        self.filename = filename
        self.version = 0
        self.width = 0
        self.height = 0
        self.fps = 0
        self.loop_count = 0
        self.frame_count = 0
        self.frames = []
        self.audio_codec = 0
        self.audio_data = b''
        self.metadata = {}

    def read(self):
        """Reads the .mpgif file and populates attributes."""
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"Fichier non trouvé: {self.filename}")

        with open(self.filename, 'rb') as f:
            header_data = f.read(HEADER_SIZE)
            if len(header_data) < HEADER_SIZE:
                 raise ValueError("Fichier invalide ou corrompu (header trop court).")

            signature, self.version, w, h, fps, fc, loop = struct.unpack(HEADER_FORMAT, header_data)
            
            if signature != SIGNATURE:
                raise ValueError(f"Signature invalide: {signature} (attendu: {SIGNATURE})")
            
            self.width = w
            self.height = h
            self.fps = fps
            self.frame_count = fc
            self.loop_count = loop

            # Read Frames
            for _ in range(self.frame_count):
                len_bytes = f.read(struct.calcsize(FRAME_HEADER_FORMAT))
                if not len_bytes:
                    break
                frame_len = struct.unpack(FRAME_HEADER_FORMAT, len_bytes)[0]
                frame_data = f.read(frame_len)
                if len(frame_data) != frame_len:
                    raise ValueError("Fichier corrompu (frame incomplète).")
                self.frames.append(frame_data)

            # Read Audio
            audio_header_size = struct.calcsize(AUDIO_HEADER_FORMAT)
            audio_header_data = f.read(audio_header_size)
            
            if audio_header_data and len(audio_header_data) == audio_header_size:
                self.audio_codec, audio_len = struct.unpack(AUDIO_HEADER_FORMAT, audio_header_data)
                if audio_len > 0:
                    self.audio_data = f.read(audio_len)

            # Read Metadata (Only if Version >= 2)
            if self.version >= VERSION_2:
                meta_len_bytes = f.read(4)
                if meta_len_bytes and len(meta_len_bytes) == 4:
                    meta_len = struct.unpack('>I', meta_len_bytes)[0]
                    if meta_len > 0:
                        meta_json = f.read(meta_len)
                        try:
                            self.metadata = json.loads(meta_json.decode('utf-8'))
                        except json.JSONDecodeError:
                            print("⚠️ Metadata corrompue (JSON invalide).")

            print(f"✅ Fichier lu (v{self.version}): {self.width}x{self.height}, {len(self.frames)} frames.")

    def get_info(self):
        info = {
            "version": self.version,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frames": self.frame_count,
            "loop": "Infini" if self.loop_count == 0 else self.loop_count,
            "audio_size": len(self.audio_data),
            "metadata": self.metadata
        }
        return info
