class MPGIFPlayer {
    constructor(canvas, url) {
        this.canvas = canvas;
        this.url = url;
        this.ctx = canvas.getContext('2d');
        this.mpgif = null;
        this.images = [];
        this.audioCtx = null;
        this.audioBuffer = null;
        this.audioSource = null;
        this.gainNode = null;
        this.interval = null;
        this.frameIdx = 0;
        this.isPlaying = false;
        this.isLoaded = false;
        this.isHovering = false;
    }

    async load(url) {
        if (url) this.url = url;
        if (this.isLoaded) return;
        try {
            const resp = await fetch(this.url);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const buffer = await resp.arrayBuffer();

            // Assume MPGIFReader is loaded globally
            this.mpgif = new MPGIFReader(buffer);
            this.mpgif.read();

            // Unpack images
            this.images = await Promise.all(this.mpgif.frames.map(src => {
                return new Promise(resolve => {
                    const img = new Image();
                    img.src = src;
                    img.onload = () => resolve(img);
                });
            }));

            // Audio Decode (Lazy load audio context?)
            // We'll init audio context on first play to avoid browser warnings
            if (this.mpgif.audioData) {
                this.audioRaw = this.mpgif.audioData.slice(0);
            }

            // Draw first frame
            this.canvas.width = this.mpgif.width;
            this.canvas.height = this.mpgif.height;
            if (this.images.length > 0) this.ctx.drawImage(this.images[0], 0, 0);

            this.isLoaded = true;
        } catch (e) {
            console.error("Load failed", e);
            throw e;
        }
    }

    // Shared Context
    static getSharedAudioCtx() {
        if (!MPGIFPlayer._sharedAudioCtx) {
            MPGIFPlayer._sharedAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        return MPGIFPlayer._sharedAudioCtx;
    }

    async initAudio() {
        if (!this.audioRaw || this.audioBuffer) return;

        this.audioCtx = MPGIFPlayer.getSharedAudioCtx();

        // Resume if suspended (browser policy)
        if (this.audioCtx.state === 'suspended') {
            try { await this.audioCtx.resume(); } catch (e) { }
        }

        try {
            // Decode needs a fresh buffer copy every time? No, decodeAudioData detaches the buffer.
            // We slice it to keep original.
            this.audioBuffer = await this.audioCtx.decodeAudioData(this.audioRaw.slice(0));
        } catch (e) { console.warn("Audio decode failed", e); }
    }

    async play(volume = 0.5) {
        if (!this.isLoaded) await this.load();
        if (this.isPlaying) return;

        await this.initAudio();
        this.isPlaying = true;

        // Audio
        if (this.audioCtx && this.audioBuffer) {
            if (this.audioSource) try { this.audioSource.stop(); } catch (e) { }
            this.audioSource = this.audioCtx.createBufferSource();
            this.audioSource.buffer = this.audioBuffer;
            this.audioSource.loop = (this.mpgif.loopCount === 0);

            this.gainNode = this.audioCtx.createGain();
            this.gainNode.gain.value = volume;

            this.audioSource.connect(this.gainNode);
            this.gainNode.connect(this.audioCtx.destination);
            this.audioSource.start();
        }

        // Video
        if (this.interval) clearInterval(this.interval);
        if (!this.mpgif) return; // Safety check
        this.interval = setInterval(() => {
            if (!this.images.length) return;
            this.frameIdx = (this.frameIdx + 1) % this.images.length;
            this.ctx.drawImage(this.images[this.frameIdx], 0, 0);
        }, 1000 / this.mpgif.fps);
    }

    stop() {
        if (!this.isPlaying) return;
        this.isPlaying = false;

        if (this.interval) clearInterval(this.interval);
        this.interval = null;

        if (this.audioSource) {
            try { this.audioSource.stop(); } catch (e) { }
            this.audioSource = null;
        }

        // Reset
        this.frameIdx = 0;
        if (this.images.length > 0) this.ctx.drawImage(this.images[0], 0, 0);
    }
}
