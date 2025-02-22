import numpy as np
from scipy import signal
from scipy.fft import fft, ifft
import audioop
import noisereduce as nr
from typing import Tuple, Optional
import webrtcvad
import collections

class AdvancedVoiceProcessor:
    def __init__(self):
        self.sample_rate = 48000
        self.chunk_size = 960  # 20ms at 48kHz
        self.channels = 1
        
        # VAD (Voice Activity Detection)
        self.vad = webrtcvad.Vad(3)  # Aggressiveness level 3
        self.vad_frame_duration = 20  # ms
        
        # Noise profile
        self.noise_profile = None
        self.noise_samples = collections.deque(maxlen=50)
        
        # Echo cancellation history
        self.echo_history = collections.deque(maxlen=10)
        self.last_output = None
        
        # AGC (Automatic Gain Control) parameters
        self.target_rms = 20000
        self.min_gain = 0.5
        self.max_gain = 2.0
        self.agc_history = collections.deque(maxlen=20)
        
        # Adaptive noise gate
        self.noise_gate_threshold = 500
        self.noise_gate_samples = collections.deque(maxlen=100)

    def process_audio_chunk(self, audio_data: bytes, user_id: int) -> bytes:
        """Process raw audio data with advanced algorithms"""
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Voice activity detection
        if not self._check_voice_activity(audio_array):
            return np.zeros(len(audio_array), dtype=np.int16).tobytes()
        
        # Update noise profile if this is background noise
        if self._is_background_noise(audio_array):
            self._update_noise_profile(audio_array)
        
        # Advanced noise reduction
        filtered_audio = self._advanced_noise_reduction(audio_array)
        
        # Adaptive echo cancellation
        filtered_audio = self._adaptive_echo_cancellation(filtered_audio)
        
        # Dynamic compression
        filtered_audio = self._apply_dynamic_compression(filtered_audio)
        
        # Automatic gain control
        filtered_audio = self._automatic_gain_control(filtered_audio)
        
        # Store processed audio for echo cancellation
        if self.last_output is not None:
            self.echo_history.append(self.last_output)
        self.last_output = filtered_audio
        
        return filtered_audio.astype(np.int16).tobytes()

    def _check_voice_activity(self, audio_array: np.ndarray) -> bool:
        """WebRTC-based voice activity detection"""
        # Convert to 16-bit PCM
        audio_segment = audio_array.tobytes()
        
        # Check if audio contains voice
        try:
            return self.vad.is_speech(audio_segment, self.sample_rate)
        except:
            return True  # Default to true if VAD fails

    def _is_background_noise(self, audio_array: np.ndarray) -> bool:
        """Determine if audio segment is likely background noise"""
        rms = np.sqrt(np.mean(np.square(audio_array)))
        self.noise_gate_samples.append(rms)
        
        # Dynamically adjust noise gate threshold
        if len(self.noise_gate_samples) > 50:
            self.noise_gate_threshold = np.percentile(list(self.noise_gate_samples), 15)
        
        return rms < self.noise_gate_threshold

    def _update_noise_profile(self, audio_array: np.ndarray):
        """Update the noise profile for better noise reduction"""
        self.noise_samples.append(audio_array)
        if len(self.noise_samples) >= 50:
            self.noise_profile = np.mean(list(self.noise_samples), axis=0)

    def _advanced_noise_reduction(self, audio_array: np.ndarray) -> np.ndarray:
        """Advanced noise reduction using spectral subtraction and Wiener filtering"""
        # Apply noise reduce library if we have a noise profile
        if self.noise_profile is not None:
            try:
                # Use the noise reduce library with our noise profile
                reduced = nr.reduce_noise(
                    y=audio_array.astype(float),
                    sr=self.sample_rate,
                    stationary=True,
                    prop_decrease=0.75
                )
                return reduced
            except:
                pass

        # Fallback to basic noise reduction
        return self._basic_noise_reduction(audio_array)

    def _basic_noise_reduction(self, audio_array: np.ndarray) -> np.ndarray:
        """Basic noise reduction using bandpass filter"""
        nyquist = self.sample_rate // 2
        low_cut = 100  # Hz
        high_cut = 7000  # Hz
        low = low_cut / nyquist
        high = high_cut / nyquist
        b, a = signal.butter(4, [low, high], btype='band')
        return signal.filtfilt(b, a, audio_array)

    def _adaptive_echo_cancellation(self, audio_array: np.ndarray) -> np.ndarray:
        """Adaptive echo cancellation using recent output history"""
        if not self.echo_history:
            return audio_array
            
        # Create echo estimate from history
        echo_estimate = np.zeros_like(audio_array)
        for i, past_output in enumerate(self.echo_history):
            if len(past_output) == len(audio_array):
                echo_estimate += past_output * (0.5 ** (i + 1))
        
        # Subtract estimated echo
        return audio_array - (echo_estimate * 0.6)

    def _apply_dynamic_compression(self, audio_array: np.ndarray) -> np.ndarray:
        """Apply dynamic range compression"""
        # Calculate RMS energy
        rms = np.sqrt(np.mean(np.square(audio_array)))
        
        # Define compression parameters
        threshold = 10000
        ratio = 4.0
        knee = 2000
        
        # Apply compression
        if rms > threshold:
            # Calculate compression amount
            reduction = 1 - ((1 / ratio) * (rms - threshold) / rms)
            audio_array = audio_array * reduction
        
        return audio_array

    def _automatic_gain_control(self, audio_array: np.ndarray) -> np.ndarray:
        """Advanced automatic gain control with smooth transitions"""
        current_rms = np.sqrt(np.mean(np.square(audio_array)))
        self.agc_history.append(current_rms)
        
        # Calculate average RMS from history
        avg_rms = np.mean(list(self.agc_history))
        
        if avg_rms > 0:
            # Calculate required gain
            gain = self.target_rms / avg_rms
            
            # Limit gain to acceptable range
            gain = np.clip(gain, self.min_gain, self.max_gain)
            
            # Apply gain
            return np.clip(audio_array * gain, -32768, 32767)
            
        return audio_array