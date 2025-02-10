import asyncio
from typing import List
from services.recording_service import RecordingService
from services.transcription_service import TranscriptionService
from services.memo_service import MemoService
from custom_types.transcript_models import Transcript
import time
import os


class TranscriptManager():
    def __init__(self, segment_duration: int = 10):
        """
        Initialize TranscriptManager
        

        Args:
            segment_duration (int): Duration of each recording segment in seconds
        """
        self.recording_service = RecordingService(device_name="Mikrofon (SXFI GAMER)")
        self.transcription_service = TranscriptionService()
        self.memo_service = MemoService()
        self.is_transcribing = False
        # Register async handler


      


    async def memo(self):
        """Main method to handle recording and transcription"""
        # Record audio and get mp3 path directly
        audio_file_path = self._record()

        # Convert to mp3 right after recording
        mp3_path = self._convert_to_mp3(audio_file_path)

        # Transcribe audio (now using mp3)
        transcript_path = await self._transcript(mp3_path)
        # Create memo
        memo = await self._memo(transcript_path)
        return memo


    def _record(self) -> str:
        audio_file = self.recording_service.record()
        return audio_file.path
    
    def _convert_to_mp3(self, audio_file_path: str) -> str:
        return self.recording_service.convert_to_mp3(audio_file_path)


    async def _transcript(self, audio_file_path: str) -> str:
        transcript = await self.transcription_service.speach_to_text(audio_file_path)

        #save transcript
        transcript_path = os.path.join(
            os.path.dirname(audio_file_path),
            "transcript.txt"
        )
        with open(transcript_path, "w", encoding='utf-8') as f:
            f.write(str(transcript))
        return transcript_path




    async def _memo(self, transcript_path: str) -> list[dict]:
        memo = await self.memo_service.extract_tasks_from_file(transcript_path)


        # Format memo as text
        memo_text = "Tasks List:\n"
        memo_text += "------------------------\n"
        for idx, task in enumerate(memo, 1):
            memo_text += f"\n{idx}. {task['title']}\n"
            memo_text += f"Description: {task['description']}\n"
            if task['assignee']:
                memo_text += f"Assignee: {task['assignee']}\n"
            memo_text += "-" * 40 + "\n"
        
        # Save formatted memo
        memo_path = os.path.join(
            os.path.dirname(transcript_path),
            "memo.txt"
        )
        with open(memo_path, "w", encoding='utf-8') as f:
            f.write(memo_text)
            
        return memo

async def test():
    manager = TranscriptManager(segment_duration=5)  # 10-second segments
    
    #mp3_file_path = manager._convert_to_mp3("D:/Ignacy/Code/AIAgents/recordings/record_20250210_173351/record_20250210_173351.wav")
    transcript_path = await manager._transcript("D:/Ignacy/Code/AIAgents/recordings/record_20250210_173351/record_20250210_173351.mp3")
    memo = await manager._memo(transcript_path)

    print("\nMemo:")
    print(memo)

async def main():

    try:

        manager = TranscriptManager(segment_duration=5)  # 10-second segments
        memo = await manager.memo()
        print("\nMemo:")
        print(memo)
    except Exception as e:

        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())











