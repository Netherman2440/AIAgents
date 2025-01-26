import asyncio
import json
import logging
from services.openai_service import OpenAIService
from prompts.extract_tasks import extract_tasks_prompt
from custom_types.transcript_models import Transcript

openai_service = OpenAIService()

async def validate_and_consolidate_tasks(tasks: list) -> list:
    validation_prompt = """You are a task management expert. Your job is to review and optimize the task list by:

0. Answer in Polish
1. Consolidating similar tasks into broader ones
2. Removing any duplicates or redundant tasks
3. Updating tasks with the most detailed version when similar tasks exist
4. Preserving all important information while making the list more concise
5. Ensuring each task has a 'description' field

Return the tasks array in JSON format where each task is an object with a 'description' field."""

    result = await openai_service.completion(
        messages=[
            {"role": "system", "content": validation_prompt},
            {"role": "user", "content": json.dumps(tasks)}
        ],
        jsonMode=True
    )
    
    return json.loads(result.choices[0].message.content)["tasks"]

async def process_transcript_in_chunks(transcript_path: str, chunk_size: int = 2000) -> list:
    # Read and create transcript object
    print(f"Reading transcript from: {transcript_path}")
    with open(transcript_path, 'r', encoding='utf-8') as file:
        text = file.read()
    transcript = Transcript.from_text(text)
    
    # Initialize variables
    current_tasks = []
    start_time = 0
    total_duration = transcript.seconds
    
    print(f"Total transcript duration: {total_duration} seconds")
    print("Starting chunk processing...\n")

    # Process transcript in chunks
    while start_time < total_duration:
        end_time = min(start_time + chunk_size, total_duration)
        chunk = transcript.slice(start_time, end_time)
        
        print(f"Processing chunk: {start_time}-{end_time} seconds")

        # Get AI response for current chunk
        result = await openai_service.completion(
            messages=[
                {"role": "system", "content": extract_tasks_prompt(json.dumps(current_tasks), "Polish")},
                {"role": "user", "content": str(chunk)}
            ],
            jsonMode=True
        )

        print(result.choices[0].message.content)

        # Parse response and append new tasks
        try:
            response_dict = json.loads(result.choices[0].message.content)
            if response_dict["tasks"]:
                current_tasks.extend(response_dict["tasks"])
            
            print("\nCurrent tasks list:")
            print(json.dumps(current_tasks, indent=2))
            print("\n" + "="*50 + "\n")
            
        except json.JSONDecodeError:
            logging.warning(f"Warning: Could not parse JSON response for chunk {start_time}-{end_time}")
            
        start_time = end_time

    # Validate and consolidate final task list
    final_tasks = await validate_and_consolidate_tasks(current_tasks)
    
    print("\nFinal task list:")
    # Pretty print numbered tasks
    for i, task in enumerate(final_tasks, 1):
        print(f"\n{i}. {task['description']}")
    print("\n")
    
    return final_tasks

async def main():
    transcript_path = "D:/Ignacy/Audio/production_22.01.2025/production_22.01.2025_full_transcript.txt"
    final_tasks = await process_transcript_in_chunks(transcript_path)

if __name__ == "__main__":
    asyncio.run(main())