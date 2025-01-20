import json
from typing import Dict, Any
from services.jira_service import JiraService
from custom_types.models import IService, UpdateIssueParams, AddIssueParams
from prompts import addtasks_prompt, update_task_prompt, list_tasks_prompt
from services.openai_service import OpenAIService
from config.jira_config import STATUSES, TASK_TYPES, EPICS, USERS

class TaskService(IService):
    def __init__(self, project_key: str):
        self.project_key = project_key
        self.jira_service = JiraService(self.project_key)
        self.openai_service = OpenAIService()

    async def execute(self, query: str):
        # Parse JSON query
        query_dict: Dict[str, Any] = json.loads(query)
        
        # Handle each operation type
        if query_dict.get("add"):
            add_tasks_response = await self.add_tasks(query_dict["add"])
            response_dict = json.loads(add_tasks_response)
            
            created_docs = []
            
            # Iterujemy po wszystkich zadaniach do utworzenia
            for task in response_dict.get("add", []):
                # Używamy parent bezpośrednio, bez dodatkowego przetwarzania
                add_params = AddIssueParams(**{
                    "summary": task["summary"],
                    "description": task.get("description"),
                    "issuetype": task.get("issuetype", "Zadanie"),
                    "priority": task.get("priority"),
                    "assignee": task.get("assignee"),
                    "reporter": task.get("reporter"),
                    "parent": task.get("parent"),  # używamy parent bezpośrednio
                    "add_to_sprint": task.get("add_to_sprint", False)
                })
                doc = self.jira_service.create_issue(add_params)
                created_docs.append(doc)
            
            return created_docs
            
        if query_dict.get("update"):
            update_tasks_response = await self.update_tasks(query_dict["update"])
            print(update_tasks_response)

            response_dict = json.loads(update_tasks_response)
            updated_docs = []
            # Iterujemy po wszystkich elementach diff
            for task_update in response_dict["diff"]:
                # Convert dictionary to UpdateIssueParams
                update_params = UpdateIssueParams(
                    task_id=task_update["task_id"],
                    **{k: v for k, v in task_update.items() if k in UpdateIssueParams.__dataclass_fields__ and k != "task_id"}
                )
                # Aktualizujemy każde zadanie i dodajemy do listy
                updated_doc = self.jira_service.update_issue(update_params)
                updated_docs.append(updated_doc)
            
            return updated_docs
            
        if query_dict.get("list"):
            list_tasks_response = await self.list_tasks(query_dict["list"])

            print(list_tasks_response)

            response_dict = json.loads(list_tasks_response)
            docs = self.jira_service.list_issues(response_dict["jql"])
            return docs

    async def add_tasks(self, query: str):
        users = USERS
        epics = EPICS
        task_types = TASK_TYPES
        prompt = addtasks_prompt(self.project_key, task_types, users, epics)
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ]
        )   
        return response.choices[0].message.content

    async def update_tasks(self, query: str):
        prompt = update_task_prompt(self.project_key, TASK_TYPES, USERS, EPICS)
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content


    async def list_tasks(self, query: str):
        prompt = list_tasks_prompt(self.project_key, TASK_TYPES, USERS, EPICS, STATUSES)
        response = await self.openai_service.completion(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content



