import asyncio
import json
import logging
import re
from services.openai_service import OpenAIService
from prompts.extract_tasks import extract_tasks_prompt
from custom_types.transcript_models import Transcript
from prompts.batch_tasks import batch_tasks_prompt

openai_service = OpenAIService()

async def extract_tasks(transcript_path: str, chunk_size: int = 0) -> list:
    """
    Main entry point for task extraction
    Args:
        transcript_path: Path to the transcript file
        chunk_size: Optional size of chunks in seconds. If None, process entire transcript at once
    """
    # Read and create transcript object
    print(f"Reading transcript from: {transcript_path}")
    with open(transcript_path, 'r', encoding='utf-8') as file:
        text = file.read()
    transcript = Transcript.from_text(text)
    
    # If no chunk_size specified, process entire transcript at once
    if chunk_size == 0:
        print("Processing entire transcript at once...")
        raw_tasks = await process_chunk(transcript)
        return await consolidate_tasks(
            raw_tasks,
            "Consolidate tasks from multiple iterations of the conversation:"
        )
    
    # Initialize variables for chunked processing
    chunks_tasks = []
    start_time = 0
    total_duration = transcript.seconds
    
    print(f"Total transcript duration: {total_duration} seconds")
    print(f"Processing in chunks of {chunk_size} seconds...\n")

    # Process transcript in chunks
    while start_time < total_duration:
        end_time = min(start_time + chunk_size, total_duration)
        chunk = transcript.slice(start_time, end_time)
        
        print(f"Processing chunk: {start_time}-{end_time} seconds")
        
        # Process chunk and consolidate its tasks
        chunk_raw_tasks = await process_chunk(chunk)
        chunk_consolidated = await consolidate_tasks(
            chunk_raw_tasks,
            "Consolidate tasks from multiple iterations of the same conversation chunk:"
        )
        chunks_tasks.append(chunk_consolidated)
        
        start_time = end_time

    # If we processed multiple chunks, consolidate them
    if len(chunks_tasks) > 1:
        # Flatten the chunks_tasks list
        all_chunk_tasks = [task for chunk in chunks_tasks for task in chunk]
        final_tasks = await consolidate_tasks(
            all_chunk_tasks,
            "Consolidate tasks from different parts of the conversation:"
        )
        return final_tasks
    
    # If we only had one chunk, return its tasks
    return chunks_tasks[0] if chunks_tasks else []

async def process_chunk(transcript_chunk: str, iterations: int = 5) -> list:
    """
    Process a single chunk multiple times and extract tasks
    Returns a list of JSON task objects
    """
    tasks_lists = []
    
    for i in range(iterations):
        print(f"\nIteration {i+1}/{iterations}")
        print("-" * 50)
        
        result = await openai_service.completion(
            messages=[
                {"role": "system", "content": extract_tasks_prompt("Polish")},
                {"role": "user", "content": str(transcript_chunk)},
            ],
            jsonMode=True
        )
        
        try:
            content = json.loads(result.choices[0].message.content)
            
            # Print reasoning field if it exists
            if "reasoning" in content:
                print("\nReasoning analysis:")
                print("-" * 20)
                print(content["reasoning"])
                print("-" * 20)
            
            if "tasks" in content and isinstance(content["tasks"], list):
                print("\nExtracted tasks:")
                print(json.dumps(content["tasks"], ensure_ascii=False, indent=2))
                tasks_lists.extend(content["tasks"])
            else:
                print("Response doesn't contain valid tasks array")
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            continue
    
    if not tasks_lists:
        logging.warning("No tasks were extracted from any iteration")
        return []
        
    return tasks_lists

async def consolidate_tasks(tasks: list, context: str) -> list:
    """
    Consolidate multiple task objects into a final task list
    Args:
        tasks: List of task objects to consolidate
        context: Description of what kind of consolidation we're doing
    """
    print("\nStarting task consolidation...")
    print("Input tasks:")
    print(json.dumps(tasks, ensure_ascii=False, indent=2))
    
    # Convert tasks to JSON string for the prompt
    tasks_json = json.dumps(tasks, ensure_ascii=False, indent=2)
    
    result = await openai_service.completion(
        messages=[
            {"role": "system", "content": batch_tasks_prompt(context, "Polish")},
            {"role": "user", "content": tasks_json}
        ],
        jsonMode=True
    )
    
    try:
        content = json.loads(result.choices[0].message.content)
        if "tasks" in content and isinstance(content["tasks"], list):
            return content["tasks"]
        else:
            logging.warning("Consolidated response doesn't contain valid tasks array")
            return []
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse consolidated JSON response: {e}")
        return []

async def main():
    transcript_path = "D:/Ignacy/Audio/production_24.01.2025/production_24.01.2025_full_transcript.txt"
    final_tasks = await extract_tasks(transcript_path, chunk_size=0)
    
    print("\nFinal consolidated tasks:")
    print("------------------------")
    if isinstance(final_tasks, list) and len(final_tasks) > 0:
        # Pretty print the full JSON tasks
        print("\nFull tasks JSON:")
        print(json.dumps(final_tasks, ensure_ascii=False, indent=2))
        
        # Print simplified task list
        print("\nSimplified task list:")
        print("------------------------")
        for idx, task in enumerate(final_tasks, 1):
            print(f"\n{idx}. {task['title']}")
            print(f"Description: {task['description']}")
            if task['assignee']:
                print(f"Assignee: {task['assignee']}")
            print("-" * 40)
    else:
        print("No tasks found.")

if __name__ == "__main__":
    asyncio.run(main())