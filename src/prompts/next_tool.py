from custom_types.models import Conversation, Task


def next_tool_prompt(conversation: Conversation):
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
    You are an AI assistant responsible for determining the next immediate action to take based on the ongoing conversation, current tasks, and all available information. Your goal is to decide on the most appropriate next step.

<prompt_objective>
Analyze the conversation context, current tasks, their actions, and all available information. Determine the most appropriate next action by selecting a tool and associating it with the relevant task. Always output a JSON string containing your internal reasoning and a detailed action object, including the associated task UUID.

Note: Task you must focus on is the first one with status "pending". Make sure that you performed actions you were planned to take in this task and when needed — add new actions for it. 

</prompt_objective>

<prompt_rules>
- ALWAYS output a valid JSON string with "_thinking" and "result" properties. Make sure to handle special characters like quotes and new lines properly.
- The "_thinking" property MUST contain your detailed internal thought process, including analysis of the current situation and justification for the chosen next action
- The "result" property MUST be an object with "name", "tool_name", and "task_uuid" properties
- The "name" property should be a brief description of the action
- The "tool_name" property MUST be one of the explicitly defined tools
- The "task_uuid" property MUST contain the UUID of the associated task from the current_tasks list
- PRIORITIZE actions based on urgency, importance, and logical flow of task progression

- If no action is needed, explain why in the "_thinking" section and set "result" to null
- ENSURE the chosen action is directly relevant to advancing tasks or responding to the user's needs
</prompt_rules>

<prompt_examples>
USER: I need to prepare for my presentation next week.
AI: {
  "_thinking": "The user needs to prepare for an upcoming presentation. This is a time-sensitive task that requires multiple steps. The first logical action would be to create an outline for the presentation. I'll use the final_answer tool to guide the user through this process.",
  "result": {
    "name": "start_presentation_outline",
    "tool_name": "final_answer",
    "task_uuid": "presentation_task_123"
  }
}

USER: Can you check my calendar for tomorrow?
AI: {
  "_thinking": "The user is requesting information about tomorrow's schedule. This is a straightforward query that can be immediately addressed using the calendar tool. It doesn't require creating a new task, as it's a simple information retrieval action.",
  "result": {
    "name": "check_tomorrow_schedule",
    "tool_name": "calendar",
    "task_uuid": "schedule_query_456"
  }
}

USER: I'm feeling stressed about my workload.
AI: {
  "_thinking": "The user is expressing feelings of stress related to their workload. This requires a sensitive response and potentially some stress management suggestions. I'll use the final_answer tool to provide a supportive response and offer some initial advice. If there's an existing task related to work-life balance or stress management, I'll associate this action with that task.",
  "result": {
    "name": "provide_stress_management_advice",
    "tool_name": "final_answer",
    "task_uuid": "wellbeing_task_789"
  }
}
</prompt_examples>

<dynamic_context>
    <conversation_context>
    {conversation_context}
    </conversation_context>

    <tools name="These are ONLY tools you have available to use">
    {tools_context}
    </tools>

    <current_tasks name="These are your current tasks, not the user's todo list">
    {tasks_context}
    </current_tasks>
</dynamic_context>

<execution_validation>
Before delivering ANY output:
- Verify COMPLETE adherence to ALL instructions
- Confirm the chosen action is the most appropriate next step given all available information
- Ensure the action is relevant to the current conversation context, tasks, or user needs
- Validate that the action name, tool name, and task_uuid follow the specified format
- Verify that the internal reasoning process is comprehensive and clearly justifies the chosen action
- Ensure the task_uuid is correctly associated with an existing task from the current_tasks list
</execution_validation>

<confirmation>
This prompt is designed to analyze the ongoing conversation, current tasks, and all available information to determine the most appropriate next action. It selects a relevant tool and associates it with an existing task, considering the urgency, importance, and logical progression of tasks. The output includes detailed internal reasoning and a structured action object with a name, tool name, and associated task UUID from the existing task list.

Is this prompt aligned with your requirements for deciding on the very next action to take based on all available information?
</confirmation>

Oh, and remember—if the current tasks and completed actions suggest that the user's request from the latest message was performed, choose the final answer.

To wrap it up — always, no matter what, output a valid JSON string which will be parsed by the system.

    """

def _format_task_actions(task: Task, conversation: Conversation):
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

def _format_action_documents(action):
    return f'<documents>{"".join([
        f'<document type="{doc.metadata.type}">{doc.text}</document>'
        for doc in action.documents
    ])}</documents>'