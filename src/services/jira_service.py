import json
import os
from jira import JIRA, Issue
from dotenv import load_dotenv
from config.jira_config import USERS
from services.document_service import DocumentService
from custom_types.models import Document, UpdateIssueParams, AddIssueParams


class JiraService():
    def __init__(self, project_key: str):
        """
        Inicjalizuje serwis Jira dla konkretnego projektu
        
        Args:
            project_key: Klucz projektu (np. 'SOE', 'PMM', etc.)
        """
               
        load_dotenv()
        
        self.jira_url = os.getenv("JIRA_URL")
        self.jira_username = os.getenv("JIRA_USERNAME")
        self.jira_api_token = os.getenv("JIRA_API_TOKEN")
        self.document_service = DocumentService()
        self.jira = JIRA(
            server=self.jira_url,
            basic_auth=(self.jira_username, self.jira_api_token)
        )
        
        self.project_key = project_key
        self.project = self.jira.project(project_key)
        
    def list_issues(self, query_jql: str):
        issues = self.jira.search_issues(query_jql)

        docs = []
        for issue in issues:
            docs.append(self.create_document(issue))

        return docs

    def update_issue(self, params: UpdateIssueParams):
        """
        Aktualizuje istniejące zgłoszenie
        
        Args:
            params: Parametry aktualizacji (UpdateIssueParams)
                task_id: Klucz zadania (np. 'SOET-123')
                summary: Nowy tytuł (opcjonalnie)
                description: Nowy opis (opcjonalnie)
                project: Nowy projekt (opcjonalnie)
                issuetype: Nowy typ zadania (opcjonalnie)
                priority: Nowy priorytet (opcjonalnie)
                assignee: Nowy assignee (opcjonalnie) - display name użytkownika
                parent: Klucz zadania nadrzędnego (opcjonalnie)
                add_to_sprint: Czy dodać do aktywnego sprintu (None = bez zmian, True = do sprintu, False = do backlogu)
        
        Returns:
            object: Zaktualizowany dokument zadania
        """
         # Import at the top of the file if not already there
        
        issue = self.jira.issue(params.task_id)
        
        # Update basic fields
        update_dict = {}
        if params.summary:
            update_dict['summary'] = params.summary
        if params.description:
            update_dict['description'] = params.description
        if params.project:
            update_dict['project'] = {'key': params.project}
        if params.issuetype:
            update_dict['issuetype'] = {'name': params.issuetype}
        if params.priority:
            update_dict['priority'] = {'name': params.priority}
        if params.assignee:
            # Look up account_id by display name
            account_id = None
            for acc_id, name in USERS.items():
                if name == params.assignee:
                    account_id = acc_id
                    break
            
            if account_id:
                update_dict['assignee'] = {'accountId': account_id}
            else:
                print(f"\033[91mWarning: Could not find account ID for user {params.assignee}\033[0m")
            
        if params.parent:
            update_dict['parent'] = {'key': params.parent}
        
        if update_dict:
            issue.update(fields=update_dict)
        
        # Handle sprint changes
        if params.add_to_sprint is not None:
            boards = self.jira.boards(projectKeyOrID=self.project_key)
            if boards:
                board_id = boards[0].id
                if params.add_to_sprint:
                    # Add to active sprint
                    active_sprints = self.jira.sprints(board_id, state='active')
                    if active_sprints:
                        sprint_id = active_sprints[0].id
                        self.jira.add_issues_to_sprint(sprint_id, [params.task_id])
                        print(f"Przeniesiono zgłoszenie {params.task_id} do aktywnego sprintu")
                    else:
                        print("Nie znaleziono aktywnego sprintu")
                else:
                    # Move to backlog
                    self.jira.move_to_backlog([params.task_id])
                    print(f"Przeniesiono zgłoszenie {params.task_id} do backlogu")
        
        print(f"Zaktualizowano zgłoszenie: {params.task_id}")
        return self.create_document(issue)

    def create_issue(self, params: AddIssueParams):
        """Create a new issue in Jira"""
        from config.jira_config import USERS  # Import at the top of the file if not already there
        
        issue_dict = {
            'project':  self.project_key,
            'summary': params.summary,
            'issuetype': params.issuetype,
        }

        if params.priority:
            issue_dict['priority'] = params.priority
        
        if params.description:
            issue_dict['description'] = params.description
            
        if params.assignee:
            # Look up account_id by display name
            account_id = None
            for acc_id, name in USERS.items():
                if name == params.assignee:
                    account_id = acc_id
                    break
            
            if account_id:
                issue_dict['assignee'] = {'accountId': account_id}
            else:
                print(f"\033[91mWarning: Could not find account ID for user {params.assignee}\033[0m")

        if params.parent:
            issue_dict['parent'] = params.parent

        # Create the issue
        new_issue = self.jira.create_issue(fields=issue_dict)
        
        if params.add_to_sprint:
            # Pobierz aktywny sprint
            boards = self.jira.boards(projectKeyOrID=self.project_key)
            if boards:
                board_id = boards[0].id
                active_sprints = self.jira.sprints(board_id, state='active')
                if active_sprints:
                    # Dodaj do pierwszego aktywnego sprintu
                    sprint_id = active_sprints[0].id
                    self.jira.add_issues_to_sprint(sprint_id, [new_issue.key])
                    print(f"Dodano zgłoszenie {new_issue.key} do aktywnego sprintu")
                else:
                    print("Nie znaleziono aktywnego sprintu")
        else:
            print(f"Dodano zgłoszenie {new_issue.key} do backlogu")
        
        return self.create_document(new_issue)
    
    def create_document(self, issue: Issue):
        # Tworzymy słownik tylko z potrzebnymi polami
        issue_dict = {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": getattr(issue.fields, 'description', ''),
            "status": issue.fields.status.name,
            "created": str(issue.fields.created),
            "updated": str(issue.fields.updated),
            "assignee": getattr(issue.fields.assignee, 'displayName', 'Unassigned'),
            "issuetype": issue.fields.issuetype.name,
            "priority": getattr(issue.fields.priority, 'name', 'None'),
        }

        doc = self.document_service.create_document(params={
            "text": json.dumps(issue_dict),
            "name": issue.fields.summary,
            "description": "This is a document created from Jira issue",
            "type": "text",
            "urls": [f"{self.jira_url}/browse/{issue.key}"] + (issue.fields.urls if hasattr(issue.fields, 'urls') else []),
            "uuid": None
        })
        return doc

    def delete_issue(self, issue_key: str) -> bool:
        """
        Usuwa zgłoszenie
        
        Args:
            issue_key: Klucz zgłoszenia (np. 'SOE-123')
        """
        try:
            self.jira.issue(issue_key).delete()
            print(f"Usunięto zgłoszenie: {issue_key}")
            return True
        except Exception as e:
            print(f"Nie można usunąć zgłoszenia {issue_key}: {str(e)}")
            return False

    def list_issue_types(self, debug: bool = False) -> list:
        """
        Wyświetla typy zgłoszeń dostępne w bieżącym projekcie
        
        Args:
            debug: Czy wyświetlać szczegółowe informacje
        """
        # Pobieramy typy zgłoszeń specyficzne dla projektu
        issue_types = self.project.issueTypes
        
        if debug:
            print(f"\nDostępne typy zgłoszeń w projekcie {self.project_key}:")
            print("------------------")
            for issue_type in issue_types:
                print(f"Nazwa: {issue_type.name}")
                print(f"ID: {issue_type.id}")
                print(f"Opis: {issue_type.description}")
                print(f"Podtyp: {'Tak' if issue_type.subtask else 'Nie'}")
                print("------------------")
        
        return issue_types

    def list_users(self, debug: bool = False) -> dict:
        """
        Wyświetla listę użytkowników dostępnych w bieżącym projekcie
        
        Args:
            debug: Czy wyświetlać szczegółowe informacje
        
        Returns:
            dict: Słownik w formacie {displayName: accountId}
        """
        users = self.jira.search_assignable_users_for_projects(username='', projectKeys=[self.project_key])
        users_dict = {}
        
        if debug:
            print(f"\nLista użytkowników projektu {self.project_key}:")
            print("------------------")
        
        for user in users:
            users_dict[user.displayName] = user.accountId
            if debug:
                print(f"Display name: {user.displayName}")
                print(f"Account ID: {user.accountId}")
                print(f"Email: {getattr(user, 'emailAddress', 'Brak')}")
                print(f"Active: {getattr(user, 'active', 'Unknown')}")
                print("------------------")
        
        return users_dict

    def list_epics(self, max_results: int = 50, debug: bool = False) -> dict:
        """
        Pobiera listę epików z projektu
        
        Args:
            max_results: Maksymalna liczba zwracanych epików
            debug: Czy wyświetlać szczegółowe informacje
        
        Returns:
            dict: Słownik w formacie {epic_key: epic_name}
        """
        jql = f'project = {self.project_key} AND issuetype = "Epic" ORDER BY created DESC'
        epics = self.jira.search_issues(jql, maxResults=max_results)
        
        epics_dict = {}
        
        if debug:
            print(f"\nLista epików w projekcie {self.project_key}:")
            print("------------------------")
        
        for epic in epics:
            epic_key = epic.key
            epic_name = epic.fields.summary
            epics_dict[epic_key] = epic_name
            
            if debug:
                print(f"[{epic_key}] {epic_name}")
                print(f"Status: {epic.fields.status.name}")
                print(f"Przypisane do: {epic.fields.assignee.displayName if epic.fields.assignee else 'Nieprzypisane'}")
                print("------------------------")
        
        return epics_dict

    def list_statuses(self, debug: bool = False) -> list:
        """
        Wyświetla listę wszystkich możliwych statusów na pierwszej tablicy projektu
        
        Args:
            debug: Czy wyświetlać szczegółowe informacje
        
        Returns:
            list: Lista wszystkich możliwych statusów
        """
        # Pobierz pierwszą tablicę projektu
        boards = self.jira.boards(projectKeyOrID=self.project_key)
        if not boards:
            print("Nie znaleziono żadnej tablicy w projekcie")
            return []
        
        board_id = boards[0].id
        
        # Pobierz wszystkie statusy z tablicy
        statuses = self.jira.statuses()
        statuses_list = [status.name for status in statuses]
        
        if debug:
            print(f"\nWszystkie możliwe statusy na tablicy {boards[0].name}:")
            print("------------------")
            for status in statuses:
                print(f"Status: {status.name}")
                print(f"ID: {status.id}")
                print(f"Kategoria: {status.statusCategory.name}")
                print("------------------")
        
        return statuses_list

    

   
if __name__ == "__main__":
    jira_service = JiraService("SOET")
    epic = jira_service.list_issue_types(True)

    
