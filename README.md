# AI Discord Bot with Jira Integration

## Overview
This Discord bot leverages AI capabilities to automatically create and manage Jira issues based on Discord conversations. The bot monitors messages, processes mentions, and interacts with users to streamline the task management workflow between Discord and Jira.

## Features
- AI-powered message processing
- Automatic Jira issue creation and management
- Discord message context awareness
- Conversation tracking and memory
- User mention handling
- Support for threaded conversations

## Prerequisites
- Python 3.x
- Discord Bot Token
- OpenAI API Key
- Jira API Access

## Required Dependencies
```
discord.py
openai
jira
python-dotenv
```

## Project Structure
```
src/
├── app.py                 # Main application file
├── services/
│   ├── discord_service.py # Discord integration
│   ├── openai_service.py  # OpenAI integration
│   └── task_service.py    # Jira task management
├── prompts/
│   ├── plan.py           # AI planning prompts
│   └── answer.py         # AI response prompts
├── config/
│   └── jira_config.py    # Jira configuration
└── custom_types/
    └── models.py         # Data models
```

## Configuration
1. Set up your Discord bot and get the token
2. Configure your OpenAI API key
3. Set up Jira API access
4. Update the configuration files with your credentials
5. Map Discord users to Jira usernames in `jira_config.py`

## Usage
1. Invite the bot to your Discord server
2. Mention the bot in a channel
3. The bot will:
   - Process your message
   - Plan appropriate actions
   - Create/update Jira issues as needed
   - Respond with confirmation and status

## Example Interactions
```
@Bot create a new task for implementing login page
@Bot what's the status of SOET-123?
@Bot update the priority of SOET-456 to high
```

## Features in Detail
- **Conversation Memory**: Maintains context for 5 minutes in the same channel
- **Thread Support**: Can respond in message threads
- **User Mapping**: Maps Discord usernames to Jira accounts
- **AI Planning**: Uses AI to determine the best course of action for each request
- **Status Updates**: Provides thinking status while processing requests

## Development
To run the bot locally:
```bash
python src/app.py
```

## Environment Variables
Create a `.env` file with:
```
DISCORD_TOKEN=your_discord_token
OPENAI_API_KEY=your_openai_key
JIRA_URL=your_jira_url
JIRA_USERNAME=your_jira_username
JIRA_API_TOKEN=your_jira_api_token
```
