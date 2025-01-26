import asyncio
from services.audio_service import AudioService

audio_service = AudioService()

#result = asyncio.run(audio_service.transcribe("D:/Ignacy/Audio/production_24.01.2025/production_24.01.2025_part1.mp3"))
#print(result)

transcript = asyncio.run(audio_service.speach_to_text("D:/Ignacy/Audio/production_24.01.2025/production_24.01.2025.mp3"))

with open("D:/Ignacy/Audio/production_24.01.2025/production_24.01.2025_full_transcript.txt", 'w', encoding='utf-8') as file:
    file.write(str(transcript))