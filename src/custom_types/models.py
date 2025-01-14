from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional, TypeVar, Generic

T = TypeVar('T')

class IService(ABC):
    @abstractmethod
    def execute(self, action: str, data: dict):
        pass

# Option 2: Using dataclass
@dataclass
class DocMetadata:
    #tokens: int
    type: Literal['audio', 'text', 'image', 'document']
    #content_type: Literal['chunk', 'complete']
    #source: Optional[str] = None
    #mimeType: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    #source_uuid: Optional[str] = None
    #conversation_uuid: Optional[str] = None
    uuid: Optional[str] = None
    #duration: Optional[float] = None
    #headers: Optional[Dict[str, List[str]]] = None
    urls: Optional[List[str]] = None
    #images: Optional[List[str]] = None
    #screenshots: Optional[List[str]] = None
    #chunk_index: Optional[int] = None
    #total_chunks: Optional[int] = None

    def dict(self) -> dict:
        return asdict(self)

@dataclass
class Document:
    text: str
    metadata: DocMetadata
    def dict(self) -> dict:
        return asdict(self)

# Definicje typów
class ContentType(str, Enum):
    COMPLETE = "complete"
    CHUNK = "chunk"
    FULL = "full"
    MEMORY = "memory"

class DocumentType(str, Enum):
    AUDIO = "audio"
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"

@dataclass
class UpdateIssueParams:
    task_id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    project: Optional[str] = None
    issuetype: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    parent: Optional[str] = None
    add_to_sprint: Optional[bool] = None

@dataclass
class AddIssueParams:
    summary: str
    description: Optional[str] = None
    issuetype: str = "Task"
    priority: str = "Medium"
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    parent: Optional[str] = None
    add_to_sprint: bool = False

@dataclass
class Task:
    uuid: str
    name: str
    description: str
    actions: List[Action]
    status: Literal['pending', 'completed', 'failed']
    

@dataclass
class Action:
    uuid: str
    name: str
    tool_uuid: str
    tool_name: str
    payload: Optional[str] = None
    result: Optional[str] = None

@dataclass
class Tool:
    uuid: str
    name: str
    description: str
    instruction: str

@dataclass
class Message:
    uuid: str
    user: str
    content: str
    created_at: datetime
    ref_uuid: Optional[str] = None

@dataclass
class Conversation:
    uuid: str
    messages: List[Message]
    tasks: List[Task]
    channel_id: str
    server_id: str
    last_message_time: datetime
    tools: List[Tool]
    

    def add_message(self, message: Message):
        self.messages.append(message)
        self.last_message_time = message.created_at