import pyaudio
import wave
import threading
import time
import os
from datetime import datetime

class AudioRecorder:
    def __init__(self, output_dir="D:/Ignacy/Audio", device_name="USB Audio Device"):
        # Audio recording parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.SEGMENT_DURATION = 15 * 60  # 15 minutes in seconds
        
        # Initialize PyAudio and find the correct device
        self.audio = pyaudio.PyAudio()
        self.device_index = self._get_device_index(device_name)
        if self.device_index is None:
            available_devices = self._list_devices()
            raise ValueError(f"Device '{device_name}' not found. Available devices:\n{available_devices}")
        
        # Recording state
        self.is_recording = False
        self.output_dir = output_dir
        self.current_segment = 1
        self.frames = []
        
        # Create timestamp-based directory for this recording session
        self.timestamp = datetime.now().strftime("%d.%m.%Y")
        self.session_dir = os.path.join(output_dir, f"production_{self.timestamp}")
        os.makedirs(self.session_dir, exist_ok=True)
    
    def _get_device_index(self, device_name):
        """Find the device index for a given device name"""
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0 and device_name.lower() in device_info['name'].lower():
                return i
        return None
    
    def _list_devices(self):
        """Return a string listing all available input devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # Only input devices
                devices.append(f"Index {i}: {device_info['name']}")
        return "\n".join(devices)
    
    def start_recording(self):
        """Start the recording process"""
        print("Starting recording...")
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()
    
    def stop_recording(self):
        """Stop the recording and save the final segment"""
        print("\nStopping recording...")
        self.is_recording = False
        self.recording_thread.join()
        
        # Save any remaining frames as the final segment
        if self.frames:
            self._save_segment(is_final=True)
        

        # Create combined file from all segments
        self._combine_segments()
        
        self.audio.terminate()
        print("Recording finished and saved!")
    
    def _record(self):
        """Main recording loop"""
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=self.device_index,  # Use selected device
            frames_per_buffer=self.CHUNK
        )
        
        segment_start_time = time.time()
        
        while self.is_recording:
            data = stream.read(self.CHUNK)
            self.frames.append(data)
            
            # Check if current segment duration exceeded
            if time.time() - segment_start_time >= self.SEGMENT_DURATION:
                self._save_segment()
                segment_start_time = time.time()
                self.frames = []
                self.current_segment += 1
        
        stream.stop_stream()
        stream.close()
    
    def _save_segment(self, is_final=False):
        """Save current y6 to a WAV file"""
        if not self.frames:  # Skip if no frames recorded
            print("No frames to save")
            return
            
        filename = os.path.join(self.session_dir, f"production_{self.timestamp}_part{self.current_segment}.wav")
        print(f"\nSaving segment: {filename}")
        
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.frames))
            
            # Verify the file was written correctly
            if os.path.getsize(filename) > 0:
                print(f"Segment saved successfully: {filename}")
            else:
                print(f"Warning: Saved segment is empty: {filename}")
                
        except Exception as e:
            print(f"Error saving segment {filename}: {str(e)}")
    
    def _combine_segments(self):
        """Combine all recorded segments into a single file"""
        segments = sorted([f for f in os.listdir(self.session_dir) if f.endswith('.wav')])
        if not segments:
            return
        
        final_filename = os.path.join(self.session_dir, f"production_{self.timestamp}.wav")
        print(f"\nCombining segments into: {final_filename}")
        
        # Use first segment to get audio parameters
        with wave.open(os.path.join(self.session_dir, segments[0]), 'rb') as wf:
            params = wf.getparams()
        
        # Create final file with same parameters
        with wave.open(final_filename, 'wb') as final_wav:
            final_wav.setparams(params)
            
            # Append all segments
            for segment in segments:
                with wave.open(os.path.join(self.session_dir, segment), 'rb') as wf:
                    final_wav.writeframes(wf.readframes(wf.getnframes()))

def main():
    try:
        # Create recorder instance with specific device
        recorder = AudioRecorder(device_name="USB Audio Device")
        print("Press Enter to start recording...")
        input()
        
        recorder.start_recording()
        print("Recording... Press Enter to stop")
        input()
        
        recorder.stop_recording()
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 