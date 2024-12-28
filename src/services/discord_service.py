import os
from discord import Intents
from discord.ext import commands
import dotenv

class DiscordService:
    def __init__(self):
        dotenv.load_dotenv()    
        self.bot = commands.Bot(command_prefix='/', intents=Intents.all())
        self.token = os.getenv("DISCORD_TOKEN")
        self._on_mention_callbacks = []  # List to store mention event callbacks
        
        # Rejestracja eventów
        @self.bot.event
        async def on_ready():
            print(f'Bot zalogowany jako {self.bot.user}')
            
        @self.bot.event
        async def on_message(message):
            
            
            if message.author == self.bot.user:
               
                return
                
            # Check if bot was mentioned
            if self.bot.user in message.mentions:
                msg = message.content.lower()
                msg = msg.replace(f'<@{self.bot.user.id}>', '').strip()
                
                # Notify all subscribers about the mention
                for callback in self._on_mention_callbacks:
                    await callback(message, msg)

            await self.bot.process_commands(message)
            
        # Przykładowa komenda
        @self.bot.command(name='ping')
        async def ping(ctx):
            await ctx.send(f'Pong! Opóźnienie: {round(self.bot.latency * 1000)}ms')
    
    def run(self):
        """Uruchamia bota Discord"""
        self.bot.run(self.token)


if __name__ == "__main__":
    discord_service = DiscordService()
    discord_service.run()