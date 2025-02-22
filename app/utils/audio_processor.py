# Opus Codec örneği (opuslib kütüphanesi ile)
import opuslib

class AudioProcessor:
    def __init__(self):
        self.encoder = opuslib.Encoder(48000, 1, 'audio')
        self.encoder.bitrate = 510000  # 510 Kbps (max for Opus)
        self.decoder = opuslib.Decoder(48000, 1)

    def encode_audio(self, pcm_data: bytes) -> bytes:
        """PCM'den Opus'a encode"""
        return self.encoder.encode(pcm_data, 960)  # 20ms frame

    def decode_audio(self, opus_data: bytes) -> bytes:
        """Opus'dan PCM'e decode"""
        return self.decoder.decode(opus_data, 960)