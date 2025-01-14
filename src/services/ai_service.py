from typing import Dict
from custom_types.models import Conversation
from prompts.next_tool import next_tool_prompt
from prompts.plan_tasks import plan_task_prompt
from services.openai_service import OpenAIService


class AIService:

    conversations: Dict[str, Conversation] = {}
    def __init__(self):
        self.openai_service = OpenAIService()
        pass

    async def plan(self, conversation: Conversation):
        #plan tasks for conversation
        prompt = plan_task_prompt(conversation)
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": conversation.messages[-1]}
            ]
        )
        #create tasks from response

        return conversation

    async def next(self, conversation: Conversation):
        # get next action for pending task in conversation
        prompt = next_tool_prompt(conversation)
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": conversation.messages[-1]}
            ]
        )
        return response.choices[0].message.content

    async def use_tool(self, conversation: Conversation):
        # use generated parameters to call tool
        pass
