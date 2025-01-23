import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import tiktoken


from prompts.summarize import summarize_prompt
from services.openai_service import OpenAIService

SPECIAL_TOKENS = {
    "<|im_start|>": 100264,
    "<|im_end|>": 100265,
    "<|im_sep|>": 100266
}

@dataclass
class TokenizerState:
    tokenizer: Optional[tiktoken.Encoding] = None
    model_name: str = "gpt-4o"

class TextService:
    def __init__(self, model_name: str = "gpt-4o"):
        self.state = TokenizerState(model_name=model_name)
        self.openai_service = OpenAIService()

    async def summarize(self, text: str | list[str]) -> str:

        if isinstance(text, list):
            formatted_text = self._format_transcription_parts(text)
        else:
            formatted_text = text

        prompt = summarize_prompt()
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": formatted_text}
            ]
        )
        return response

    def _format_transcription_parts(self, file_paths: List[str]) -> str:
        """
        Reads and formats multiple transcription files into a single formatted string.
        
        Args:
            file_paths: List of paths to transcription files
        
        Returns:
            Formatted string containing all transcription parts
        """
        formatted_text = ""
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read().strip()
                    formatted_text += f"<part{i}>\n{content}\n</part{i}>\n\n"
            except FileNotFoundError:
                print(f"Warning: File not found - {file_path}")
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")
                
        return formatted_text




