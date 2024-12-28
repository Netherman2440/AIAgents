import os
from typing import Literal
from jira import JIRA
from dotenv import load_dotenv


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
        
        self.jira = JIRA(
            server=self.jira_url,
            basic_auth=(self.jira_username, self.jira_api_token)
        )
        
        self.project_key = project_key
        self.project = self.jira.project(project_key)
        

    def list_issues(self, max_results: int = 50, status: Literal["To Do", "In Progress", "Done"] = None) -> list:
        """
        Pobiera listę zgłoszeń z projektu
        
        Args:
            max_results: Maksymalna liczba zwracanych zgłoszeń
            status: Opcjonalny filtr po statusie (np. 'To Do', 'In Progress', 'Done')
        """
        jql = f"project = {self.project_key}"
        if status:
            jql += f" AND status = '{status}'"
        jql += " ORDER BY created DESC"
        
        issues = self.jira.search_issues(jql, maxResults=max_results)
        
        for issue in issues:
            print(f"[{issue.key}] {issue.fields.summary}")
            print(f"Status: {issue.fields.status.name}")
            print(f"Przypisane do: {issue.fields.assignee.displayName if issue.fields.assignee else 'Nieprzypisane'}")
            print("------------------------")
        
        return issues

    def create_issue(self, summary: str, description: str, 
                    issue_type: str = "Task", 
                    assignee: str = None) -> object:
        """
        Tworzy nowe zgłoszenie
        
        Args:
            summary: Tytuł zgłoszenia
            description: Opis zgłoszenia
            issue_type: Typ zgłoszenia (domyślnie 'Task')
            assignee: Opcjonalnie - nazwa użytkownika do przypisania
        """
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type}
        }
        
        if assignee:
            issue_dict['assignee'] = {'name': assignee}
            
        new_issue = self.jira.create_issue(fields=issue_dict)
        print(f"Utworzono zgłoszenie: {new_issue.key}")
        return new_issue

    def update_issue(self, issue_key: str, 
                    summary: str = None, 
                    description: str = None, 
                    status: str = None,
                    assignee: str = None) -> object:
        """
        Aktualizuje istniejące zgłoszenie
        
        Args:
            issue_key: Klucz zgłoszenia (np. 'SOE-123')
            summary: Nowy tytuł (opcjonalnie)
            description: Nowy opis (opcjonalnie)
            status: Nowy status (opcjonalnie)
            assignee: Nowy assignee (opcjonalnie)
        """
        issue = self.jira.issue(issue_key)
        
        update_dict = {}
        
        if summary:
            issue.update(summary=summary)
        
        if description:
            issue.update(description=description)
            
        if assignee:
            issue.update(assignee={'name': assignee})
            
        if status:
            transitions = self.jira.transitions(issue)
            for t in transitions:
                if t['name'].lower() == status.lower():
                    self.jira.transition_issue(issue, t['id'])
                    break
        
        print(f"Zaktualizowano zgłoszenie: {issue_key}")
        return issue

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

    def list_issue_types(self):
        """
        Wyświetla typy zgłoszeń dostępne w bieżącym projekcie
        """
        # Pobieramy typy zgłoszeń specyficzne dla projektu
        issue_types = self.project.issueTypes
        
        print(f"\nDostępne typy zgłoszeń w projekcie {self.project_key}:")
        print("------------------")
        for issue_type in issue_types:
            print(f"Nazwa: {issue_type.name}")
            print(f"ID: {issue_type.id}")
            print(f"Opis: {issue_type.description}")
            print(f"Podtyp: {'Tak' if issue_type.subtask else 'Nie'}")
            print("------------------")
        
        return issue_types

    def list_users(self):
        """
        Wyświetla listę u��ytkowników dostępnych w bieżącym projekcie
        """
        users = self.jira.search_assignable_users_for_projects(username= '',projectKeys=[self.project_key])
        
        print(f"\nLista użytkowników projektu {self.project_key}:")
        print("------------------")
        for user in users:
            print(user)
           
        
        return users

    def list_epics(self, max_results: int = 50) -> list:
        """
        Pobiera listę epików z projektu
        
        Args:
            max_results: Maksymalna liczba zwracanych epików
        """
        # W Jirze epiki są identyfikowane przez issuetype = Epik
        jql = f'project = {self.project_key} AND issuetype = "Epik" ORDER BY created DESC'
        
        print(f"Wykonywane zapytanie JQL: {jql}")  # Debug info
        epics = self.jira.search_issues(jql, maxResults=max_results)
        
        print(f"\nLista epików w projekcie {self.project_key}:")
        print("------------------------")
        for epic in epics:
            print(f"[{epic.key}] {epic.fields.summary}")
            print(f"Status: {epic.fields.status.name}")
            print(f"Przypisane do: {epic.fields.assignee.displayName if epic.fields.assignee else 'Nieprzypisane'}")
            print("------------------------")
        
        return epics

   
if __name__ == "__main__":
    jira_service = JiraService("SOET")
    jira_service.list_epics()  # użyj ID ze screenshota

