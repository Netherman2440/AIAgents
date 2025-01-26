import base64
import os
import dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
class OpenAIService:
    def __init__(self):
        dotenv.load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)


    async def completion(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str = "gpt-4o",
        jsonMode: bool = False,
        
        stream: bool = False
    ):
   
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            
        response_format= { "type": "json_object" } if jsonMode else { "type": "text" },
        stream=stream
        )
        return response

    def tokenizer(self, text: str) -> int:
        """
        Liczy liczbę tokenów w tekście używając tokenizera GPT-2.
        
        Args:
            text: Tekst do zliczenia tokenów
            
        Returns:
            int: Liczba tokenów w tekście
        """
        try:
            from transformers import GPT2TokenizerFast
            tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
            return len(tokenizer(text)["input_ids"])
        except Exception as e:
            raise Exception(f"Error while counting tokens: {str(e)}")

    async def transcribe_audio(
        self, 
        audio_file_path: str,
        use_timestamps: bool = False,
        prompt: str = None
    ) -> str | dict:
        """
        Transcribes audio file using OpenAI Whisper API.
        
        Args:
            audio_file_path: Path to audio file
            use_timestamps: Whether to use timestamps in transcription
            prompt: Optional helper text for the model (max 244 tokens)
                   Can contain context hints, specialized vocabulary,
                   or expected transcription format.
            
        Returns:
            str | dict: Raw transcription from Whisper API
                       Returns str when use_timestamps=False
                       Returns dict when use_timestamps=True
            
        Raises:
            ValueError: When file is larger than 25MB or prompt exceeds 244 tokens
        """
        if prompt:
            token_count = self.tokenizer(prompt)
            if token_count > 244:
                raise ValueError(f"Prompt cannot exceed 244 tokens. Current token count: {token_count}")
            
        if os.path.getsize(audio_file_path) > 25 * 1024 * 1024:
            raise ValueError("Audio file is too large. Maximum size is 25MB.")
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json" if use_timestamps else "text",
                    timestamp_granularities=["segment"] if use_timestamps else None,
                    prompt=prompt
                )
                return transcript
                
        except Exception as e:
            raise Exception(f"Transcription error: {str(e)}")
        
