from typing import List, Optional, Dict, Any, TypedDict, Literal
from uuid import uuid4
import json
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from custom_types.models import ContentType, DocMetadata, DocumentType, Document
from services.text_service import TextService





class CreateDocumentParams:
    text: str
    type: Literal['audio', 'text', 'image', 'document']
    name: Optional[str] = None
    description: Optional[str] = None
    uuid: Optional[str] = None
    urls: Optional[List[str]] = None

class ValidationError(Exception):
    def __init__(self, message: str, context: Dict[str, Any]):
        self.message = message
        self.context = context
        super().__init__(self.message)

class DocumentService:
    def __init__(self):
        #self.text_service = TextService()
        pass
    def create_document(self, params: CreateDocumentParams) -> Document:
        """
        Tworzy nowy dokument.
        """
        document_uuid = params.get('uuid') or str(uuid4())

        # Przygotowanie metadanych
        metadata = DocMetadata(
            uuid=document_uuid,
            type=params.get('type'),
            name=params.get('name'),
            description=params.get('description'),
            urls=params.get('urls')
        )

        document = Document(
            text=params.get('text'),
            metadata=metadata
        )
        
        return document

    async def _after_create_hook(self, document: Dict[str, Any]) -> None:
        """
        Hook wywoływany po utworzeniu dokumentu.
        """
        # Implementacja hooków
        pass

    def _map_to_document_type(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mapuje surowy dokument na właściwy typ dokumentu.
        """
        try:
            metadata = (
                json.loads(document["metadata"])
                if isinstance(document["metadata"], str)
                else document["metadata"]
            )
            
            return {
                **document,
                "metadata": DocMetadata(**metadata).dict()
            }
        except Exception as e:
            raise ValidationError(
                "Failed to parse document metadata",
                {"document_uuid": document["uuid"], "error": str(e)}
            )
