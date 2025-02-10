import asyncio
import pyaudio
import wave
import threading
import time
import os
from datetime import datetime
from typing import Callable, List, Optional
from custom_types.audio_file import AudioFile
from pydub import AudioSegment


class RecordingService:
    def __init__(self,  device_name: str = "USB Audio Device"):
        """
        Initialize the RecordingService
        
        Args:
            device_name (str): Name of the input audio device to use for recording
        """
        # Audio recording parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        # Initialize PyAudio and find the correct device
        self.audio = pyaudio.PyAudio()
        self.device_index = self._get_device_index(device_name)
        if self.device_index is None:
            available_devices = self._list_devices()
            raise ValueError(f"Device '{device_name}' not found. Available devices:\n{available_devices}")
        
        # Recording state
        self.is_recording = False
        self.output_dir = "recordings"
        self.frames = []

    def record(self, name: Optional[str] = None) -> AudioFile:
        """
        Start recording with optional custom name
        
        Args:
            name: Optional custom name for the recording
            
        Returns:
            AudioFile: Path to the WAV file
        """
        if self.is_recording:
            raise RuntimeError("Recording is already in progress")

        print("Press Enter to start recording...")
        input()

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recording_name = name or f"record_{self.timestamp}"
        self.session_dir = os.path.join(self.output_dir, self.recording_name)
        os.makedirs(self.session_dir, exist_ok=True)

        # WAV file path
        wav_path = os.path.join(
            self.session_dir, 
            f"{self.recording_name}.wav"
        )

        try:
            self._record_to_wav(wav_path)
            return AudioFile(wav_path)
        except Exception as e:
            if os.path.exists(wav_path):
                os.remove(wav_path)
            raise e

    def _record_to_wav(self, wav_path: str):
        """Record audio to WAV file"""
        self.is_recording = True
        self.frames = []
        
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.CHUNK
        )

        print("Recording... Press Enter to stop")
        
        stop_event = threading.Event()
        
        def wait_for_stop():
            input()
            stop_event.set()
            
        input_thread = threading.Thread(target=wait_for_stop)
        input_thread.daemon = True
        input_thread.start()
        
        try:
            while self.is_recording and not stop_event.is_set():
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                self.frames.append(data)
        finally:
            self.is_recording = False
            stream.stop_stream()
            stream.close()
            self.audio.terminate()

            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.frames))

    def convert_to_mp3(self, wav_path: str) -> str:
        """
        Convert WAV file to MP3 with optimized settings and keep both files
        
        Args:
            wav_path: Path to the input WAV file
            
        Returns:
            str: Path to the converted MP3 file
        """
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"WAV file not found: {wav_path}")


        # Create MP3 filename from WAV path
        mp3_path = os.path.splitext(wav_path)[0] + '.mp3'

        try:
            print("Starting conversion to MP3...")
            # Convert to MP3 with optimized settings
            audio = AudioSegment.from_wav(wav_path)
            print("WAV file loaded successfully")
            
            audio.export(
                mp3_path,
                format="mp3",
                parameters=[
                    "-b:a", "128k",  # Bitrate 128kbps
                    "-q:a", "0",     # Use highest quality VBR mode
                ]
            )
            print("MP3 export completed")
            
            # Verify the MP3 file was created successfully
            if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) == 0:
                raise RuntimeError("MP3 file was not created successfully")
            
            # Print file size information only if conversion was successful
            wav_size = os.path.getsize(wav_path) / (1024 * 1024)  # MB
            mp3_size = os.path.getsize(mp3_path) / (1024 * 1024)  # MB
            print(f"\nRecording saved as:")
            print(f"WAV: {wav_path}")
            print(f"MP3: {mp3_path}")
            print(f"WAV size: {wav_size:.1f}MB")
            print(f"MP3 size: {mp3_size:.1f}MB")
            print(f"Compression ratio: {wav_size/mp3_size:.1f}x")
            
            return mp3_path
            
        except Exception as e:
            print(f"Error during MP3 conversion: {str(e)}")

            if os.path.exists(mp3_path):
                os.remove(mp3_path)  # Clean up failed MP3 file
            raise

    def _get_device_index(self, device_name: str) -> Optional[int]:
        """Find the device index for a given device name"""
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0 and device_name.lower() in device_info['name'].lower():
                return i
        return None

    def _list_devices(self) -> str:
        """Return a string listing all available input devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                devices.append(f"Index {i}: {device_info['name']}")
        return "\n".join(devices)

    # Remove or comment out stop_recording method as it's no longer needed
    # async def stop_recording(self):
    #     ...

    # Remove or comment out _save_segment method as it's no longer needed
    # def _save_segment(self, frames, is_final: bool = False) -> Optional[AudioFile]:
    #     ... 

    

    