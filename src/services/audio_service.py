import asyncio
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import os

from services.openai_service import OpenAIService

class AudioService:
    
    def __init__(self):
        self.openai_service = OpenAIService()
        
        # Prompt for Whisper API - focused on business meeting context and proper punctuation
        self.transcription_prompt = """This is a business meeting transcript. 
Multiple people are speaking, discussing projects and exchanging ideas.
The conversation includes typical business language like: ROI, KPI, deadline, milestone, stakeholder.
Speakers often interrupt each other saying: "I agree", "Let me add", "If I may...", "Excuse me".

Example style:
John: I think we should focus on the Q3 deliverables.
Sarah: Yes, and let me add that the ROI metrics show...
John: If I may interrupt - what about the stakeholder feedback?
Sarah: Good point. Let's discuss that first."""

        self.speach_to_text_prompt = """
   - Improve the context and clarity of the business meeting transcription:
   - Maintain the conversation flow between multiple speakers
   - Keep the timestamps to indicate speaker changes
   - Clean up speech disfluencies while preserving meaning


Return the Polish translation with timestamps preserved."""
    
    async def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribes audio file, improves context, translates to Polish and saves to txt files.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            str: Path to the final translated text file
            
        Raises:
            Exception: If processing fails
        """
        try:
            # Get transcription with timestamps
            print(f"Starting transcription of: {audio_file_path}")
            transcript = await self.openai_service.transcribe_audio(
                audio_file_path,
                use_timestamps=True,
                prompt=self.transcription_prompt
            )
            
            # Save raw transcription
            raw_transcript_path = os.path.splitext(audio_file_path)[0] + '_raw.txt'
            with open(raw_transcript_path, 'w', encoding='utf-8') as f:
                if isinstance(transcript, str):
                    f.write(transcript)
                else:
                    # Format JSON response with timestamps
                    formatted_text = ""
                    for segment in transcript.segments:
                        start_time = f"{int(segment.start // 60):02d}:{int(segment.start % 60):02d}"
                        formatted_text += f"[{start_time}] {segment.text.strip()}\n"
                    f.write(formatted_text)
            
            print(f"Raw transcription saved to: {raw_transcript_path}")
            
            # Improve and translate using completion
            print("Processing and translating transcript...")
            response = await self.openai_service.completion(
                messages=[
                    {"role": "system", "content": self.speach_to_text_prompt},
                    {"role": "user", "content": formatted_text if 'formatted_text' in locals() else str(transcript)}
                ]
            )
            
            # Save final translation
            final_path = os.path.splitext(audio_file_path)[0] + '_translated.txt'
            with open(final_path, 'w', encoding='utf-8') as f:
                f.write(response.choices[0].message.content)
            
            print(f"Translation saved to: {final_path}")
            return final_path
            
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            raise Exception(f"Failed to process audio file: {str(e)}")

    def segment_audio_at_silence(self, input_file):
        """
        Segments audio file into 10 minute chunks if file is larger than 25MB,
        otherwise returns original file path
        
        Args:
            input_file (str): Path to the input audio file
            
        Returns:
            list: Paths to the segmented audio files or list with original file path
        """
        # Check file size
        file_size_mb = os.path.getsize(input_file) / (1024 * 1024)  # Convert to MB
        
        if file_size_mb <= 25:
            print(f"\nFile size ({file_size_mb:.2f}MB) is under 25MB limit. Skipping segmentation.")
            return [input_file]
            
        print(f"\nStarting audio segmentation for: {input_file}")
        print(f"File size: {file_size_mb:.2f}MB")
        
        # Define parameters
        duration_minutes = 10   # segment length in minutes
        min_silence_len = 500  # minimum silence length in ms
        silence_thresh = -50   # silence threshold in dB
        search_window = 60000  # search window for silence (60 seconds)
        
        # Load the audio file
        print("Loading audio file...")
        audio = AudioSegment.from_file(input_file)
        print(f"Audio loaded. Duration: {len(audio)/1000:.2f} seconds")
        
        # Convert minutes to milliseconds
        target_length = duration_minutes * 60 * 1000
        
        # Get file name without extension
        filename, ext = os.path.splitext(input_file)
        
        segments = []
        start = 0
        segment_count = 1
        
        while start < len(audio):
            print(f"\nProcessing segment {segment_count}")
            print(f"Current position: {start/1000:.2f} seconds")
            
            # Define the search region for silence
            end_target = min(start + target_length, len(audio))
            search_start = max(end_target - search_window, 0)
            search_end = min(end_target + search_window, len(audio))
            search_region = audio[search_start:search_end]
            
            print(f"Searching for silence between {search_start/1000:.2f}s and {search_end/1000:.2f}s")
            
            if end_target >= len(audio):
                print("Reached end of audio file")
                segment = audio[start:]
                output_path = f"{filename}_part{len(segments)+1}{ext}"
                print(f"Exporting final segment to: {output_path}")
                segment.export(output_path, format=ext.replace('.', ''))
                segments.append(output_path)
                break
                
            # Find silent regions
            silent_ranges = detect_nonsilent(
                search_region,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh,
                seek_step=1
            )
            
            if silent_ranges:
                # Convert nonsilent ranges to silent ranges
                silent_ranges = self._get_silent_ranges(silent_ranges, len(search_region))
                
                # Find the longest silence
                longest_silence = max(silent_ranges, key=lambda x: x[1] - x[0])
                silence_length = longest_silence[1] - longest_silence[0]
                
                # Use the middle of the longest silence as the cut point
                silence_midpoint = longest_silence[0] + silence_length // 2
                cut_point = start + target_length - search_window + silence_midpoint
                
                print(f"Found longest silence: {silence_length/1000:.2f}s at {cut_point/1000:.2f}s")
            else:
                cut_point = end_target
                print("No silence found, cutting at target length")
            
            # Extract and export segment
            segment = audio[start:cut_point]
            output_path = f"{filename}_part{len(segments)+1}{ext}"
            print(f"Exporting segment {segment_count} to: {output_path}")
            print(f"Segment duration: {len(segment)/1000:.2f} seconds")
            
            segment.export(output_path, format=ext.replace('.', ''))
            segments.append(output_path)
            
            start = cut_point
            segment_count += 1
        
        print(f"\nSegmentation complete. Created {len(segments)} segments.")
        return segments

    def _get_silent_ranges(self, nonsilent_ranges, total_length):
        """Helper method to convert nonsilent ranges to silent ranges"""
        silent_ranges = []
        
        # If no nonsilent ranges, the whole region is silent
        if not nonsilent_ranges:
            return [(0, total_length)]
        
        # Add silent range before first nonsilent range
        if nonsilent_ranges[0][0] > 0:
            silent_ranges.append((0, nonsilent_ranges[0][0]))
        
        # Add silent ranges between nonsilent ranges
        for i in range(len(nonsilent_ranges)-1):
            silent_ranges.append((nonsilent_ranges[i][1], nonsilent_ranges[i+1][0]))
        
        # Add silent range after last nonsilent range
        if nonsilent_ranges[-1][1] < total_length:
            silent_ranges.append((nonsilent_ranges[-1][1], total_length))
        
        return silent_ranges

    

# Example usage
if __name__ == "__main__":
    audio_service = AudioService()
    asyncio.run(audio_service.transcribe("D:/Ignacy/Audio/audio_part5.mp3"))

