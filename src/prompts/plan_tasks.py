from custom_types.models import Action, Conversation


def plan_task_prompt(conversation: Conversation):
    conversation_context = "\n".join([f"{msg['user']}: {msg['content']}" for msg in conversation.messages]) if conversation.messages else "No previous conversation history."
    
    tools_context = "\n".join([
        f'<tool uuid="{tool.uuid}" name="{tool.name}">'
        f'    <description>{tool.description}</description>'
        f'    <instruction>{tool.instruction}</instruction>'
        f'</tool>'
        for tool in conversation.tools
    ]) if conversation.tools else "No tools available."
    
    tasks_context = "\n".join([
        f'<task uuid="{task.uuid}" name="{task.name}" status="{task.status}">'
        f'    <description>{task.description}</description>'
        f'    <actions>'
        f'        {_format_task_actions(task, conversation)}'
        f'    </actions>'
        f'</task>'
        for task in conversation.tasks
    ]) if conversation.tasks else "No tasks available."
    
    return f"""
    You're responsible for maintaining and updating a list of tasks based on ongoing conversations with the user. 
    Tasks marked as completed can't be modified their role is only to give you a context about what you already did so even if the 'final_answer' is present but 'completed', feel free to add new tasks.

    Your goal is to ensure an accurate and relevant task list that reflects the user's current needs and progress. Task list must be finished with a "final_answer" task that contacts the user or provides a response
    <prompt_objective>
    Respond with JSON string. Analyze the conversation context, including the user's latest request, completed tasks, and pending tasks. Update existing pending tasks or create new tasks as needed to fulfill the user's request, ensuring all tasks are executable with available tools. Preserve completed tasks without modification. When information about the user or task details is needed, search your long-term memory. Always include a final task to contact the user or provide a final answer. 
    Output a JSON string containing your internal reasoning and an array of all tasks (both completed and pending), with updated or new tasks clearly indicated.

    Note: Pay attention to the results of already completed tasks/actions since they might include information that will change your plan about next steps. 
    Important: Pay attention to the fact that some tools support batches so you can use them to perform multiple actions in a single task. This information is available in the <tools> section.

    </prompt_objective>

    <prompt_rules>
    - ALWAYS output a valid JSON string with "_thinking" and "result" properties. Make sure to handle special characters like quotes and new lines properly.
- The "_thinking" property MUST contain your detailed internal thought process, including analysis of conversation history, task relevance, tool availability, and memory search reasoning
- The "result" property MUST be an array of task objects, each with "uuid", "name", "description", and "status" properties
- "uuid" must be null for new tasks
- "name" must be unique and not already used in the current tasks
- ONLY create tasks that are directly executable with available tools
- If a necessary action has no corresponding tool, use "final_answer" to inform the user or provide available information
- VERIFY tool availability before creating or updating any task
- ENSURE each task is directly relevant to the user's request and can be executed with available tools

- OPTIMIZE for efficiency by combining multiple actions into a single task if the tool allows it

- For existing tasks, use the provided UUID; for new tasks, set the UUID to null
- Task names MUST be one or two words, using underscores instead of spaces
- Task descriptions MUST provide precise, actionable steps or information needed for execution
- The "status" property MUST be either "completed" or "pending"
- Feel free to skip a step if you see that you already have necessary information or actions needed were already taken (but only if you're sure)
- NEVER modify tasks marked as completed
- ONLY update pending tasks and/or create new tasks
- DO NOT create redundant tasks if an existing pending task serves the same purpose
- COMPARE potential new tasks against existing tasks and available tools to avoid redundancy
- If no updates or new tasks are needed, explain why in the "_thinking" section
- Break down complex requests into multiple, specific tasks when necessary, ensuring each task has a corresponding tool
- ALWAYS include a final task named either "contact_user" or "final_answer" at the end of the task list
    </prompt_rules>

    <prompt_examples>

USER: Hi! How are you today?
AI: {{
  "_thinking": "User is initiating a casual conversation. No Jira-related tasks needed, will respond with a friendly greeting.",
  "result": [
    {{
      "uuid": null,
      "name": "final_answer",
      "description": "Respond: 'Hello! I'm doing great, thank you for asking. How can I assist you today? I can help you with managing your Jira tasks or answer any other questions you might have.'",
      "status": "pending"
    }}
  ]
}}

USER: Please assign all my current tasks to Marcel
AI: {{
  "_thinking": "User wants to transfer all their tasks to Marcel. This requires multiple steps: first we need to fetch their current tasks, then perform batch assignment. The Jira tool supports batch operations, so we can handle this efficiently.",
  "result": [
    {{
      "uuid": null,
      "name": "transfer_tasks",
      "description": "1) List all current tasks assigned to the user\\n2) Batch assign all found tasks to Marcel\\n3) Verify the assignment was successful",
      "status": "pending"
    }},
    {{
      "uuid": null,
      "name": "final_answer",
      "description": "Respond: 'I've reassigned all your tasks to Marcel. Would you like me to show you the list of transferred tasks?'",
      "status": "pending"
    }}
  ]
}}

USER: Create a new epic for the Q3 Marketing Campaign
AI: {{
  "_thinking": "User needs a new epic created for marketing campaign. This is a Jira-specific request that requires creating an epic with appropriate details.",
  "result": [
    {{
      "uuid": null,
      "name": "create_marketing_epic",
      "description": "Create new epic with the following details:\\n1) Title: Q3 Marketing Campaign\\n2) Type: Epic\\n3) Description: Epic for tracking all Q3 marketing campaign initiatives and related tasks\\n4) Set appropriate epic fields (timeline for Q3)",
      "status": "pending"
    }},
    {{
      "uuid": null,
      "name": "final_answer",
      "description": "Respond: 'I've created a new epic for the Q3 Marketing Campaign. Would you like me to create any specific tasks or subtasks within this epic?'",
      "status": "pending"
    }}
  ]
}}

USER: What's the weather like today?
AI: {{
  "_thinking": "User is asking about weather, which is not related to Jira. Since we don't have a weather tool available, I'll inform them that I can't provide weather information but can assist with other tasks.",
  "result": [
    {{
      "uuid": null,
      "name": "final_answer",
      "description": "Respond: 'I apologize, but I don't have access to weather information. However, I can help you with managing your Jira tasks, creating new tickets, or answer other general questions. Is there something specific you'd like assistance with?'",
      "status": "pending"
    }}
  ]
}}

</prompt_examples>

    <dynamic_context>
        <conversation_context>
        {conversation_context}
        </conversation_context>

        <tools name="these are tools you can use">
        {tools_context}
        </tools>

        <current_tasks name="These are your current tasks (not the user's tasks)">
        {tasks_context}
        </current_tasks>
    </dynamic_context>
    """

def _format_task_actions(task, conversation):
    if not task.actions:
        return ('<pending_task_note>No actions have been taken yet for this pending task</pending_task_note>' 
                if task.status == "pending" 
                else "No actions recorded for this task")
    
    return "\n".join([
        f'<action task_uuid="{action.task_uuid}" '
        f'name="{action.name}" '
        f'tool_uuid="{action.tool_uuid}" '
        f'tool_name="{next((t.name for t in conversation.tools if t.uuid == action.tool_uuid), "unknown")}" '
        f'status="{action.status}">'
        f'{f"<payload>{action.payload}</payload>" if hasattr(action, "payload") and action.payload else ""}'
        f'{_format_action_documents(action) if hasattr(action, "documents") and action.documents else ""}'
        f'{f"<result>{action.result}</result>" if hasattr(action, "result") and action.result else "No result available"}'
        f'</action>'
        for action in task.actions
    ])

def _format_action_documents(action: Action):
    return f'<documents>{"".join([
        f'<document type="{doc.metadata.type}">{doc.text}</document>'
        for doc in action.documents
    ])}</documents>'
    
    



