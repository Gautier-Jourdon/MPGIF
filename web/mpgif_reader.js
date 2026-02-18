class MPGIFReader {
    constructor(arrayBuffer) {
        this.data = new DataView(arrayBuffer);
        this.offset = 0;
        this.width = 0;
        this.height = 0;
        this.fps = 0;
        this.frameCount = 0;
        this.loopCount = 0;
        this.frames = []; // Array of Blobs (WebP)
        this.audioData = null; // ArrayBuffer (Opus/AAC)
        this.audioCodec = 0;
    }

    read() {
        const signature = this.readString(5);
        if (signature !== "MPGIF") throw new Error("Invalid signature: " + signature);

        const version = this.data.getUint8(this.offset++);
        this.width = this.data.getUint16(this.offset, false); this.offset += 2;
        this.height = this.data.getUint16(this.offset, false); this.offset += 2;
        this.fps = this.data.getUint8(this.offset++);
        this.frameCount = this.data.getUint32(this.offset, false); this.offset += 4;
        this.loopCount = this.data.getUint8(this.offset++);

        console.log(`Parsed Header: ${this.width}x${this.height} @ ${this.fps}fps, ${this.frameCount} frames`);

        for (let i = 0; i < this.frameCount; i++) {
            const frameLen = this.data.getUint32(this.offset, false); this.offset += 4;
            const frameBytes = new Uint8Array(this.data.buffer, this.offset, frameLen);
            this.offset += frameLen;

            const blob = new Blob([frameBytes], { type: 'image/webp' });
            this.frames.push(URL.createObjectURL(blob));
        }

        if (this.offset < this.data.byteLength) {
            this.audioCodec = this.data.getUint8(this.offset++);
            const audioLen = this.data.getUint32(this.offset, false); this.offset += 4;

            if (audioLen > 0) {
                this.audioData = this.data.buffer.slice(this.offset, this.offset + audioLen);
                this.offset += audioLen;
                console.log(`Parsed Audio: ${audioLen} bytes, Codec: ${this.audioCodec}`);
            }
        }
    }

    readString(length) {
        let str = "";
        for (let i = 0; i < length; i++) {
            str += String.fromCharCode(this.data.getUint8(this.offset++));
        }
        return str;
    }
}
