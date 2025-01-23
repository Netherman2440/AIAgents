import asyncio
from services.openai_service import OpenAIService
from prompts.extract_tasks import extract_tasks_prompt

openai_service = OpenAIService()

async def extract_tasks(transcript_path: str) -> str:
    with open(transcript_path, 'r', encoding='utf-8') as file:
        transcript = file.read()

    result = await openai_service.completion(
        messages=[
        {"role": "system", "content": extract_tasks_prompt()},
        {"role": "user", "content": transcript}
    ]
)

    return result.choices[0].message.content

result = asyncio.run(extract_tasks("D:/Ignacy/Audio/production_22.01.2025/production_22.01.2025_translated.txt"))
print(result)