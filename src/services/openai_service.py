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