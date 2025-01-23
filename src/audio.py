import asyncio
import os
from services.audio_service import AudioService
from services.text_service import TextService

class AudioProcessor:

    def __init__(self):
        self.audio_service = AudioService()
        self.text_service = TextService()

    async def process_audio_file(self, audio_file_path: str) -> str:
        """
        Process audio file end-to-end: segment if needed, transcribe all parts, and generate summary.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            str: Path to the final summary file
        """
        try:
            # Step 1: Segment audio if needed
            print("Starting audio processing pipeline...")
            audio_segments = self.audio_service.segment_audio_at_silence(audio_file_path)
            
            # Step 2: Transcribe all segments and combine transcriptions
            print("\nTranscribing segments and combining...")
            translated_files = []
            combined_transcript = ""
            last_end_time = 0
            
            for segment_path in audio_segments:
                # Transcribe segment
                translated_file = await self.audio_service.transcribe(segment_path)
                translated_files.append(translated_file)
                
                # Read raw transcript and adjust timestamps
                raw_transcript_path = os.path.splitext(segment_path)[0] + '_raw.txt'
                with open(raw_transcript_path, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
                
                # Adjust timestamps and combine
                adjusted_transcript = self._adjust_timestamps(transcript_text, last_end_time)
                combined_transcript += adjusted_transcript + "\n"
                
                # Update last end time
                last_timestamp = self._get_last_timestamp(transcript_text)
                if last_timestamp:
                    last_end_time += last_timestamp
            
            # Save combined transcript
            filename = os.path.splitext(audio_file_path)[0]
            combined_path = f"{filename}_full_transcript.txt"
            with open(combined_path, 'w', encoding='utf-8') as f:
                f.write(combined_transcript)
            print(f"\nCombined transcript saved to: {combined_path}")
            
            # Step 3: Generate and save summary
            print("\nGenerating final summary...")
            summary_result = await self.text_service.summarize(translated_files)
            summary_content = summary_result.choices[0].message.content
            
            # Save summary
            summary_path = f"{filename}_summary.txt"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            print(f"\nSummary saved to: {summary_path}")
            
            return summary_path
            
        except Exception as e:
            print(f"Error during audio processing: {str(e)}")
            raise Exception(f"Failed to process audio file: {str(e)}")

    def _adjust_timestamps(self, transcript: str, offset_seconds: float) -> str:
        """
        Adjust timestamps in transcript by adding offset
        """
        adjusted_lines = []
        for line in transcript.split('\n'):
            if line.strip():
                if line.startswith('['):
                    # Extract timestamp
                    timestamp_str = line[1:6]  # Get "MM:SS"
                    minutes, seconds = map(int, timestamp_str.split(':'))
                    total_seconds = minutes * 60 + seconds + offset_seconds
                    
                    # Convert back to MM:SS format
                    new_minutes = int(total_seconds // 60)
                    new_seconds = int(total_seconds % 60)
                    new_timestamp = f"[{new_minutes:02d}:{new_seconds:02d}]{line[7:]}"
                    adjusted_lines.append(new_timestamp)
                else:
                    adjusted_lines.append(line)
                    
        return '\n'.join(adjusted_lines)

    def _get_last_timestamp(self, transcript: str) -> float:
        """
        Get the last timestamp from transcript in seconds
        """
        last_timestamp = 0
        for line in transcript.split('\n'):
            if line.startswith('['):
                timestamp_str = line[1:6]  # Get "MM:SS"
                minutes, seconds = map(int, timestamp_str.split(':'))
                last_timestamp = minutes * 60 + seconds
        return last_timestamp
    

audioProcessor = AudioProcessor()

asyncio.run(audioProcessor.process_audio_file("D:/Ignacy/Audio/production_22.01.2025/production_22.01.2025.mp3"))

