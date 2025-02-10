from dataclasses import dataclass
from pydub import AudioSegment
import os

@dataclass
class AudioFile:
    path: str
    _audio: AudioSegment = None

    def __post_init__(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Audio file not found at path: {self.path}")
        
        # Get file extension
        file_extension = os.path.splitext(self.path)[1].lower()
        
        try:
            if file_extension == '.wav':
                self._audio = AudioSegment.from_wav(self.path)
            elif file_extension == '.mp3':
                self._audio = AudioSegment.from_mp3(self.path)
            else:
                raise ValueError(f"Unsupported audio format: {file_extension}")
        except Exception as e:
            raise RuntimeError(f"Failed to load audio file: {str(e)}")

    @property
    def audio(self) -> AudioSegment:
        return self._audio 