import asyncio
import websockets
import sounddevice as sd
import numpy as np
import queue
import threading
import json
import argparse

class VoiceTestClient:
    def __init__(self, websocket_url: str, token: str, room_id: int):
        self.websocket_url = f"{websocket_url}?token={token}"
        self.room_id = room_id
        self.sample_rate = 48000
        self.chunk_size = 960  # 20ms at 48kHz
        self.channels = 1
        
        # Queues for audio data
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Audio stream active flags
        self.is_recording = False
        self.is_playing = False

    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if status:
            print(f"Audio input status: {status}")
        if self.is_recording:
            self.input_queue.put(indata.copy())

    def audio_output_callback(self, outdata, frames, time, status):
        """Callback for audio output"""
        if status:
            print(f"Audio output status: {status}")
        try:
            data = self.output_queue.get_nowait()
            outdata[:] = data.reshape(outdata.shape)
        except queue.Empty:
            outdata.fill(0)

    async def receive_audio(self, websocket):
        """Handle incoming audio from WebSocket"""
        while True:
            try:
                audio_data = await websocket.recv()
                if isinstance(audio_data, bytes):
                    # Convert bytes to numpy array
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    audio_array = audio_array.reshape(-1, self.channels)
                    self.output_queue.put(audio_array)
            except Exception as e:
                print(f"Error receiving audio: {e}")
                break

    async def send_audio(self, websocket):
        """Send audio from input queue to WebSocket"""
        while True:
            try:
                if not self.input_queue.empty():
                    audio_data = self.input_queue.get()
                    # Convert to bytes and send
                    await websocket.send(audio_data.tobytes())
                else:
                    await asyncio.sleep(0.01)
            except Exception as e:
                print(f"Error sending audio: {e}")
                break

    async def run(self):
        """Main run loop"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                print(f"Connected to room {self.room_id}")
                self.is_recording = True
                self.is_playing = True

                # Start audio streams
                with sd.InputStream(
                    channels=self.channels,
                    samplerate=self.sample_rate,
                    blocksize=self.chunk_size,
                    callback=self.audio_callback
                ), sd.OutputStream(
                    channels=self.channels,
                    samplerate=self.sample_rate,
                    blocksize=self.chunk_size,
                    callback=self.audio_output_callback
                ):
                    # Create tasks for sending and receiving audio
                    receive_task = asyncio.create_task(self.receive_audio(websocket))
                    send_task = asyncio.create_task(self.send_audio(websocket))

                    try:
                        await asyncio.gather(receive_task, send_task)
                    except KeyboardInterrupt:
                        print("\nStopping...")
                    finally:
                        receive_task.cancel()
                        send_task.cancel()

        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.is_recording = False
            self.is_playing = False

def main():
    parser = argparse.ArgumentParser(description='Voice chat test client')
    parser.add_argument('--url', default='ws://localhost:8000/ws/voice', help='WebSocket server URL')
    parser.add_argument('--token', required=True, help='Authentication token')
    parser.add_argument('--room', type=int, required=True, help='Room ID')
    
    args = parser.parse_args()
    
    client = VoiceTestClient(args.url, args.token, args.room)
    asyncio.run(client.run())

if __name__ == "__main__":
    main()