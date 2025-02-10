import json
import logging
from typing import List, Optional

from custom_types.transcript_models import Transcript
from services.openai_service import OpenAIService
from prompts.extract_tasks import extract_tasks_prompt
from prompts.batch_tasks import batch_tasks_prompt

class MemoService:
    def __init__(self):
        # Initialize OpenAI service
        self.openai_service = OpenAIService()

    async def extract_tasks_from_file(self, transcript_path: str, chunk_size: int = 0) -> List[dict]:
        """
        Main entry point for task extraction from a file
        Args:
            transcript_path: Path to the transcript file
            chunk_size: Optional size of chunks in seconds. If 0, process entire transcript at once
        Returns:
            List of consolidated tasks
        """
        # Read and create transcript object
        print(f"Reading transcript from: {transcript_path}")
        with open(transcript_path, 'r', encoding='utf-8') as file:
            text = file.read()
        transcript = Transcript.from_text(text)
        
        return await self.extract_tasks(transcript, chunk_size)

    async def extract_tasks(self, transcript: Transcript, chunk_size: int = 0) -> List[dict]:
        """
        Extract tasks from a transcript object
        Args:
            transcript: Transcript object
            chunk_size: Optional size of chunks in seconds. If 0, process entire transcript at once
        Returns:
            List of consolidated tasks
        """
        # If no chunk_size specified, process entire transcript at once
        if chunk_size == 0:
            print("Creating memo from entire transcript...")
            raw_tasks = await self._process_chunk(transcript)
            return await self._consolidate_tasks(
                raw_tasks,
                "Consolidate tasks from multiple iterations of the conversation:"
            )
        
        return await self._process_chunked_transcript(transcript, chunk_size)

    async def _process_chunked_transcript(self, transcript: Transcript, chunk_size: int) -> List[dict]:
        """
        Process transcript in chunks
        """
        chunks_tasks = []
        start_time = 0
        total_duration = transcript.seconds
        
        print(f"Total transcript duration: {total_duration} seconds")
        print(f"Processing in chunks of {chunk_size} seconds...\n")

        while start_time < total_duration:
            end_time = min(start_time + chunk_size, total_duration)
            chunk = transcript.slice(start_time, end_time)
            
            print(f"Processing chunk: {start_time}-{end_time} seconds")
            
            chunk_raw_tasks = await self._process_chunk(chunk)
            chunk_consolidated = await self._consolidate_tasks(
                chunk_raw_tasks,
                "Consolidate tasks from multiple iterations of the same conversation chunk:"
            )
            chunks_tasks.append(chunk_consolidated)
            
            start_time = end_time

        # If we processed multiple chunks, consolidate them
        if len(chunks_tasks) > 1:
            all_chunk_tasks = [task for chunk in chunks_tasks for task in chunk]
            return await self._consolidate_tasks(
                all_chunk_tasks,
                "Consolidate tasks from different parts of the conversation:"
            )
        
        return chunks_tasks[0] if chunks_tasks else []

    async def _process_chunk(self, transcript_chunk: str, iterations: int = 5) -> List[dict]:
        """
        Process a single chunk multiple times and extract tasks
        """
        tasks_lists = []
        total_tasks_per_iteration = []
        
        for i in range(iterations):
            print(f"\nIteration {i+1}/{iterations}")
            print("-" * 50)
            
            result = await self.openai_service.completion(
                messages=[
                    {"role": "system", "content": extract_tasks_prompt("Polish")},
                    {"role": "user", "content": str(transcript_chunk)},
                ],
                jsonMode=True
            )
            
            try:
                content = json.loads(result.choices[0].message.content)
                
                if "reasoning" in content:
                    print("\nReasoning analysis:")
                    print("-" * 20)
                    print(content["reasoning"])
                    print("-" * 20)
                
                if "tasks" in content and isinstance(content["tasks"], list):
                    iteration_tasks = content["tasks"]
                    total_tasks_per_iteration.append(len(iteration_tasks))
                    print(f"\nExtracted tasks in iteration {i+1}: {len(iteration_tasks)}")
                    print(json.dumps(content["tasks"], ensure_ascii=False, indent=2))
                    tasks_lists.extend(iteration_tasks)
                else:
                    print("Response doesn't contain valid tasks array")
                    total_tasks_per_iteration.append(0)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {e}")
                total_tasks_per_iteration.append(0)
                continue
        
        if not tasks_lists:
            logging.warning("No tasks were extracted from any iteration")
            return []
        
        # Print summary statistics
        print("\nTask extraction summary:")
        print("-" * 20)
        print(f"Total tasks before consolidation: {len(tasks_lists)}")
        print("Tasks per iteration:", total_tasks_per_iteration)
        print(f"Average tasks per iteration: {sum(total_tasks_per_iteration)/len(total_tasks_per_iteration):.1f}")
            
        return tasks_lists

    async def _consolidate_tasks(self, tasks: List[dict], context: str) -> List[dict]:
        """
        Consolidate multiple task objects into a final task list
        """
        print("\nStarting task consolidation...")
        print(f"Input tasks count: {len(tasks)}")
        
        # Return empty list if no tasks to consolidate
        if not tasks:
            print("No tasks to consolidate")
            return []
        
        tasks_json = json.dumps(tasks, ensure_ascii=False, indent=2)
        
        result = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": batch_tasks_prompt(context, "Polish")},
                {"role": "user", "content": tasks_json}
            ],
            jsonMode=True
        )
        
        try:
            content = json.loads(result.choices[0].message.content)
            if "tasks" in content and isinstance(content["tasks"], list):
                consolidated_tasks = content["tasks"]
                print(f"\nTasks after consolidation: {len(consolidated_tasks)}")
                # Calculate reduction ratio only if there were input tasks
                if len(tasks) > 0:
                    print(f"Reduction ratio: {len(consolidated_tasks)/len(tasks):.1%}")
                return consolidated_tasks
            else:
                logging.warning("Consolidated response doesn't contain valid tasks array")
                return []
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse consolidated JSON response: {e}")
            return [] 