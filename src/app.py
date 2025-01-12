import json
from services.openai_service import OpenAIService
from prompts.plan import plan_prompt
from config.jira_config import DISCORD_USERS, EPICS, STATUSES
from services.task_service import TaskService
from services.discord_service import DiscordService, MessageObserver, MentionObserver
from prompts.answer import answer_prompt
from discord import Message
from datetime import datetime, timedelta, timezone

from custom_types.models import Conversation



class AIDiscordBot(MessageObserver, MentionObserver):
    """
    Implementuje oba protokoły: MessageObserver i MentionObserver
    """
    def __init__(self):
        self.discord_service = DiscordService()
        self.openai_service = OpenAIService()
        self.project_key = "SOET"
        
        # Rejestracja observerów
        self.discord_service.attach_message_observer(self)
        self.discord_service.attach_mention_observer(self)
        self.conversations = []

    async def on_message(self, subject: DiscordService, message: Message) -> None:
        """
        Implementacja MessageObserver.on_message
        Wywoływana dla każdej wiadomości (która nie jest wzmianką)
        """
        print(f"Otrzymano nową wiadomość: {message.content}")
        print(f"Autor wiadomości: {message.author.name}")
        print(f"Kanał: {message.channel.name}")
        print(f"ID kanału: {message.channel.id}")
        print(f"ID wiadomości: {message.id}")
        print(f"ID autora: {message.author.id}")
        print(f"Treść wiadomości: {message.content}")
        print(f"Czas wysłania: {message.created_at}")
        print(f"Referencja: {message.reference}")

    async def on_mention(self, subject: DiscordService, message: Message, cleaned_content: str) -> None:
        """
        Implementacja MentionObserver.on_mention
        Wywoływana tylko gdy bot jest wspomniany w wiadomości
        """
        # Sprawdzenie czy wiadomość jest odpowiedzią
        reference = message.reference
        if reference and reference.message_id:
            original_message = await message.channel.fetch_message(reference.message_id)
            print(f"Ta wiadomość jest odpowiedzią na: {original_message.content}")
            print(f"Autor oryginalnej wiadomości: {original_message.author.name}")
            
            await subject.send_message(
                message.channel.id,
                "Widzę, że odpowiadasz na wcześniejszą wiadomość!",
                reply_to_message=original_message
            )
        
        # Get Jira username from Discord username
        discord_name = message.author.name.lower()
        if discord_name not in DISCORD_USERS:
            print(f"\033[91mWarning: User {discord_name} not found in DISCORD_USERS dictionary\033[0m")
            jira_username = "Unknown User"
        else:
            jira_username = DISCORD_USERS[discord_name]
            
        formatted_msg = f"{jira_username}: {cleaned_content}"
        
        conversation = self.get_conversation(
            message.guild.id if message.guild else 0,
            message.channel.id
        )   
        # Pierwsza odpowiedź - thinking
        await subject.send_message(
            message.channel.id,
            "*Thinking...*"
        )
        
        # Planowanie akcji
        actions = await self.plan(formatted_msg, conversation)

        conversation.add_message(jira_username, formatted_msg, message.created_at)


        actions_dict = json.loads(actions)
        
        # Druga odpowiedź - thinking details
        await subject.send_message(
            message.channel.id,
            f"*{actions_dict['_thinking']}*"
        )
        
        # Wykonanie akcji
        context = await self.execute(actions)
        print(context)
        
        # Finalna odpowiedź
        ai_message = await self.answer(formatted_msg,jira_username, actions, context, conversation)
        await subject.send_message(
            message.channel.id,
            ai_message,
            mention_users=[message.author]
        )

        # Dodaj wiadomość do konwersacji
        conversation.add_message("ai", ai_message, message.created_at)
        

    async def plan(self, query: str, conversation: Conversation):
        prompt = plan_prompt(self.project_key, EPICS, STATUSES, conversation)
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content

    async def execute(self, query: str):
        task_service = TaskService()
        return await task_service.execute(query)

    async def answer(self, formatted_msg, jira_username, actions, context, conversation: Conversation):
        prompt = answer_prompt(jira_username, actions, context, conversation)
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": formatted_msg}
            ]
        )
        return response.choices[0].message.content

    def get_conversation(self, server_id: int, channel_id: int) -> Conversation:
        # Szukaj istniejącej aktywnej konwersacji
        for conv in self.conversations:
            if (conv.server_id == server_id and 
                conv.channel_id == channel_id and 
                conv.last_message_time and 
                datetime.now(timezone.utc) - conv.last_message_time < timedelta(minutes=5)):
                return conv
        
        # Jeśli nie znaleziono aktywnej konwersacji, utwórz nową
        new_conv = Conversation(server_id, channel_id)
        self.conversations.append(new_conv)
        return new_conv

if __name__ == "__main__":
    bot = AIDiscordBot()
    bot.discord_service.run()   








