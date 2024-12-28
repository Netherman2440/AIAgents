import json
from typing import Dict, Any
from types.types import IService

class TaskService(IService):
    def __init__(self):
        pass

    def execute(self, query: str):
        # Parse JSON query
        query_dict: Dict[str, Any] = json.loads(query)
        
        # Handle each operation type
        if query_dict.get("add"):
            self.add_tasks(query_dict["add"])
            
        if query_dict.get("update"):
            self.update_tasks(query_dict["update"])
            
        if query_dict.get("delete"):
            self.delete_tasks(query_dict["delete"])
            
        if query_dict.get("list"):
            self.list_tasks(query_dict["list"])
            
        if query_dict.get("get"):
            self.get_task_details(query_dict["get"])

    def add_tasks(self, query: str):
        
        pass

    def update_tasks(self, query: str):
        pass

    def delete_tasks(self, query: str):
        pass

    def list_tasks(self, query: str):
        pass

    def get_task_details(self, query: str):
        pass


