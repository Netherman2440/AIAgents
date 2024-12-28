from services.openai_service import OpenAIService
from prompts.plan import plan_prompt

import os
from discord import Intents
from discord.ext import commands
import dotenv

class DiscordServices:
    def __init__(self):
        dotenv.load_dotenv()    
        self.bot = commands.Bot(command_prefix='/', intents=Intents.all())
        self.openai_service = OpenAIService()
        self.token = os.getenv("DISCORD_TOKEN")
        

      
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
                response = await self.plan(msg)
                await message.channel.send(response)

                
                    
            await self.bot.process_commands(message)
            
        # Przykładowa komenda
        @self.bot.command(name='ping')
        async def ping(ctx):
            await ctx.send(f'Pong! Opóźnienie: {round(self.bot.latency * 1000)}ms')
    
    def run(self):
        """Uruchamia bota Discord"""
        self.bot.run(self.token)

    async def plan(self, query: str):
        prompt = plan_prompt()
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ]
        )

        return response.choices[0].message.content

if __name__ == "__main__":
    discord_service = DiscordServices()
    discord_service.run()







