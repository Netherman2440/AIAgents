from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import timedelta

@dataclass
class TranscriptSegment:
    """Represents a single segment of transcribed text with timestamp"""
    timestamp_seconds: int
    text: str
    speaker: Optional[str] = None

    @property
    def timestamp(self) -> str:
        """Returns formatted timestamp as [MM:SS]"""
        minutes = self.timestamp_seconds // 60
        seconds = self.timestamp_seconds % 60
        return f"[{minutes:02d}:{seconds:02d}]"

    def with_offset(self, offset_seconds: int) -> 'TranscriptSegment':
        """Creates new segment with added time offset"""
        return TranscriptSegment(
            timestamp_seconds=self.timestamp_seconds + offset_seconds,
            text=self.text,
            speaker=self.speaker
        )

    def __str__(self) -> str:
        if self.speaker:
            return f"{self.timestamp} {self.speaker}: {self.text}"
        return f"{self.timestamp} {self.text}"

@dataclass
class Transcript:
    """Collection of transcript segments with utility methods"""
    segments: List[TranscriptSegment]

    @property
    def seconds(self) -> int:
        """Returns total duration of transcript in seconds"""
        if not self.segments:
            return 0
        return self.segments[-1].timestamp_seconds

    @classmethod
    def from_text(cls, text: str) -> 'Transcript':
        """Parse transcript text into Transcript object"""
        segments = []
        for line in text.strip().split('\n'):
            if line.strip():
                # Extract [MM:SS] timestamp
                timestamp_str = line[1:6]  # Get "MM:SS" part
                minutes, seconds = map(int, timestamp_str.split(':'))
                timestamp_seconds = minutes * 60 + seconds
                
                # Extract text after timestamp
                text = line[8:].strip()
                
                segments.append(TranscriptSegment(timestamp_seconds, text))
        return cls(segments)

    def with_offset(self, offset_seconds: int) -> 'Transcript':
        """Creates new transcript with added time offset to all segments"""
        return Transcript([
            segment.with_offset(offset_seconds) 
            for segment in self.segments
        ])

    def merge(self, other: 'Transcript') -> 'Transcript':
        """Merge another transcript after this one"""
        if not self.segments:
            return other
        if not other.segments:
            return self

        offset = self.segments[-1].timestamp_seconds
        offset_transcript = other.with_offset(offset)
        
        return Transcript(self.segments + offset_transcript.segments)

    def shuffle_with(self, other: 'Transcript') -> 'Transcript':
        """Merge two transcripts chronologically"""
        merged_segments = self.segments + other.segments
        merged_segments.sort(key=lambda x: x.timestamp_seconds)
        return Transcript(merged_segments)

    def slice(self, start_seconds: int, end_seconds: Optional[int] = None) -> 'Transcript':
        """
        Extract transcript segment between start and end time.
        If end_time is None, extracts until the end.
        Returns new Transcript with adjusted timestamps starting from 0
        """

        if start_seconds < 0:
            raise ValueError("Start time cannot be negative")
        
        if end_seconds is not None and end_seconds < start_seconds:
            raise ValueError("End time cannot be before start time")
        

        # Filter segments within time range
        filtered_segments = [
            segment for segment in self.segments
            if segment.timestamp_seconds >= start_seconds
            and (end_seconds is None or segment.timestamp_seconds <= end_seconds)
        ]
        
        # Create new segments with adjusted timestamps
        adjusted_segments = [
            TranscriptSegment(
                timestamp_seconds=segment.timestamp_seconds - start_seconds,
                text=segment.text,
                speaker=segment.speaker
            )
            for segment in filtered_segments
        ]
        
        return Transcript(adjusted_segments)

    def __str__(self) -> str:
        return '\n'.join(str(segment) for segment in self.segments)

    def dict(self) -> dict:
        return {
            'segments': [asdict(segment) for segment in self.segments],
            'duration_seconds': self.seconds
        }

    @staticmethod
    def merge_many(transcripts: list['Transcript']) -> 'Transcript':
        """Merges multiple transcripts sequentially"""
        if not transcripts:
            return Transcript([])
            
        result = transcripts[0]
        for transcript in transcripts[1:]:
            result = result.merge(transcript)
        return result

if __name__ == "__main__":
    # Read transcript file
    with open("D:/Ignacy/Audio/production_22.01.2025/production_22.01.2025_full_transcript.txt", 'r', encoding='utf-8') as file:
        transcript_text = file.read()

    # Create transcript object
    transcript = Transcript.from_text(transcript_text)
    
    print("=== Original Transcript ===")
    print(transcript)  # This will use __str__ method
    
    print("=== Original Transcript Info ===")
    print(f"Duration: {transcript.seconds} seconds")
    print(f"Number of segments: {len(transcript.segments)}")
    print("\nFirst 3 segments:")
    for segment in transcript.segments[:3]:
        print(segment)
    
    print("\n=== Sliced Transcript (2-3 minute) ===")
    slice_2_3min = transcript.slice(120, 180)
    print(f"Slice duration: {slice_2_3min.seconds} seconds")
    print("Segments:")
    print(slice_2_3min)
    
    # Create test transcript for merge/shuffle operations
    test_transcript = Transcript.from_text("""
[00:05] Test message 1
[00:15] Test message 2
[00:25] Test message 3""".strip())
    
    print("\n=== Merged Transcripts ===")
    merged = transcript.merge(test_transcript)
    print(f"Merged duration: {merged.seconds} seconds")
    print("Last 3 segments:")
    for segment in merged.segments[-3:]:
        print(segment)
    
    print("\n=== Shuffled Transcripts ===")
    shuffled = transcript.shuffle_with(test_transcript)
    print(f"Shuffled duration: {shuffled.seconds} seconds")
    print("First 5 segments:")
    for segment in shuffled.segments[:5]:
        print(segment) 