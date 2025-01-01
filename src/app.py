import json
from services.openai_service import OpenAIService
from prompts.plan import plan_prompt
from prompts.addtasks import addtasks_prompt
from config.jira_config import DISCORD_USERS, EPICS, STATUSES, USERS
import os
from discord import Intents
from discord.ext import commands
import dotenv

from services.task_service import TaskService
from custom_types.models import AddIssueParams
from services.jira_service import JiraService
from prompts.answer import answer_prompt

class DiscordServices:
    def __init__(self):
        dotenv.load_dotenv()    
        self.bot = commands.Bot(command_prefix='/', intents=Intents.all())
        self.openai_service = OpenAIService()
        self.token = os.getenv("DISCORD_TOKEN")
        self.project_key = "SOET"

      
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
                
                # Get Jira username from Discord username, use "Unknown User" if not found
                discord_name = message.author.name.lower()  # Discord names are case-sensitive
                if discord_name not in DISCORD_USERS:
                    print(f"\033[91mWarning: User {discord_name} not found in DISCORD_USERS dictionary\033[0m")
                    jira_username = "Unknown User"
                else:
                    jira_username = DISCORD_USERS[discord_name]
                    
                formatted_msg = f"{jira_username}: {msg}"
                
                # Dodanie kursywy do pierwszej odpowiedzi
                await message.channel.send("*Thinking...*")
                actions = await self.plan(formatted_msg)
                
                # Parse the actions string into a dictionary and dodanie kursywy
                actions_dict = json.loads(actions)
                await message.channel.send(f"*{actions_dict['_thinking']}*")

                context = await self.execute(actions)
                
                print(context)

                # Ostatnia odpowiedź bez kursywy, ale z pingiem użytkownika
                ai_message = await self.answer(formatted_msg, jira_username, actions, context)
                await message.channel.send(f"{message.author.mention} {ai_message}")
                    
            await self.bot.process_commands(message)
            
        # Przykładowa komenda
        @self.bot.command(name='ping')
        async def ping(ctx):
            await ctx.send(f'Pong! Opóźnienie: {round(self.bot.latency * 1000)}ms')
    
    def run(self):
        """Uruchamia bota Discord"""
        self.bot.run(self.token)

    async def answer(self, formatted_msg, jira_username,actions, context):

        prompt = answer_prompt(formatted_msg, jira_username, actions, context)
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": formatted_msg}
            ]
        )

        return response.choices[0].message.content


    async def plan(self, query: str):
        prompt = plan_prompt(self.project_key, EPICS, STATUSES)
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





if __name__ == "__main__":
    discord_service = DiscordServices()
    discord_service.run()   








