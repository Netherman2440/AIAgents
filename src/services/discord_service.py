from __future__ import annotations
from typing import Protocol, Set
from discord import Message, Intents
from discord.ext import commands
import os
import dotenv

class MessageObserver(Protocol):
    async def on_message(self, subject: DiscordService, message: Message) -> None: ...

class MentionObserver(Protocol):
    async def on_mention(self, subject: DiscordService, message: Message, cleaned_content: str) -> None: ...

class DiscordService:
    def __init__(self):
        dotenv.load_dotenv()    
        self.bot = commands.Bot(command_prefix='/', intents=Intents.all())
        self.token = os.getenv("DISCORD_TOKEN")
        self._message_observers: Set[MessageObserver] = set()
        self._mention_observers: Set[MentionObserver] = set()

        @self.bot.event
        async def on_ready():
            print(f'Bot zalogowany jako {self.bot.user}')
            
        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return
                
            # Powiadom obserwatorów o nowej wiadomości
            await self._notify_message_observers(message)
                
            # Sprawdź czy bot został wspomniany
            if self.bot.user in message.mentions:
                cleaned_content = message.content.lower()
                cleaned_content = cleaned_content.replace(f'<@{self.bot.user.id}>', '').strip()
                await self._notify_mention_observers(message, cleaned_content)

            await self.bot.process_commands(message)

    def attach_message_observer(self, observer: MessageObserver) -> None:
        """Dodaje obserwatora wiadomości"""
        self._message_observers.add(observer)
    
    def attach_mention_observer(self, observer: MentionObserver) -> None:
        """Dodaje obserwatora wzmianek"""
        self._mention_observers.add(observer)
    
    def detach_message_observer(self, observer: MessageObserver) -> None:
        """Usuwa obserwatora wiadomości"""
        self._message_observers.discard(observer)
    
    def detach_mention_observer(self, observer: MentionObserver) -> None:
        """Usuwa obserwatora wzmianek"""
        self._mention_observers.discard(observer)

    async def _notify_message_observers(self, message: Message) -> None:
        """Powiadamia wszystkich obserwatorów o nowej wiadomości"""
        for observer in self._message_observers:
            await observer.on_message(self, message)

    async def _notify_mention_observers(self, message: Message, cleaned_content: str) -> None:
        """Powiadamia wszystkich obserwatorów o wzmiance"""
        for observer in self._mention_observers:
            await observer.on_mention(self, message, cleaned_content)

    async def send_message(self, channel_id: int, content: str, 
                          reply_to_message: Message | None = None, 
                          mention_users: list | None = None) -> None:
        """
        Wysyła wiadomość na określony kanał z dodatkowymi opcjami
        
        Args:
            channel_id: ID kanału Discord
            content: Treść wiadomości
            reply_to_message: Obiekt discord.Message na który chcemy odpowiedzieć
            mention_users: Lista obiektów discord.User lub ID użytkowników do oznaczenia
        """
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        
        # Dodaj wzmianki użytkowników do treści
        if mention_users:
            mentions = []
            for user in mention_users:
                if isinstance(user, int):
                    mentions.append(f"<@{user}>")
                else:
                    mentions.append(user.mention)
            content = f"{' '.join(mentions)} {content}"
        
        # Wyślij wiadomość
        if reply_to_message:
            await reply_to_message.reply(content)
        else:
            await channel.send(content)

    def run(self):
        """Uruchamia bota Discord"""
        self.bot.run(self.token)