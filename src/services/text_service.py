from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from custom_types.models import Document
import tiktoken
from uuid import uuid4
from datetime import datetime
import re
from pydantic import BaseModel

SPECIAL_TOKENS = {
    "<|im_start|>": 100264,
    "<|im_end|>": 100265,
    "<|im_sep|>": 100266
}

@dataclass
class TokenizerState:
    tokenizer: Optional[tiktoken.Encoding] = None
    model_name: str = "gpt-4o"

class TextService:
    def __init__(self, model_name: str = "gpt-4o"):
        self.state = TokenizerState(model_name=model_name)

    def format_for_tokenization(self, text: str) -> str:
        return f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant<|im_end|>"

    def count_tokens(self, text: str) -> int:
        if not self.state.tokenizer:
            raise ValueError("Tokenizer not initialized")
        return len(self.state.tokenizer.encode(text, allowed_special=SPECIAL_TOKENS.keys()))

    async def initialize_tokenizer(self, model: Optional[str] = None) -> None:
        if not self.state.tokenizer or model != self.state.model_name:
            model_name = model or self.state.model_name
            self.state.tokenizer = tiktoken.encoding_for_model(model_name)
            self.state.model_name = model_name

    def extract_headers(self, text: str) -> Dict[str, List[str]]:
        headers: Dict[str, List[str]] = {}
        header_regex = re.compile(r'(^|\n)(#{1,6})\s+(.*)', re.MULTILINE)
        
        for match in header_regex.finditer(text):
            level = len(match.group(2))
            content = match.group(3).strip()
            key = f"h{level}"
            if key not in headers:
                headers[key] = []
            headers[key].append(content)
            
        return headers

    def update_headers(self, current: Dict[str, List[str]], 
                      extracted: Dict[str, List[str]]) -> Dict[str, List[str]]:
        updated = current.copy()
        
        for level in range(1, 7):
            key = f"h{level}"
            if key in extracted:
                updated[key] = extracted[key]
                # Usuń wszystkie nagłówki niższego poziomu
                for l in range(level + 1, 7):
                    updated.pop(f"h{l}", None)
                    
        return updated

    def extract_urls_and_images(self, text: str) -> Dict[str, Any]:
        urls: List[str] = []
        images: List[str] = []
        
        def replace_images(match):
            nonlocal images
            alt_text, url = match.groups()
            images.append(url)
            return f"![{alt_text}]({{{{$img{len(images)-1}}}}})"
            
        def replace_urls(match):
            nonlocal urls
            link_text, url = match.groups()
            if not url.startswith("{{$img"):
                urls.append(url)
                return f"[{link_text}]({{{{$url{len(urls)-1}}}}})"
            return match.group(0)
            
        # Najpierw zastąp obrazy
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_images, text)
        # Następnie zastąp URLe
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_urls, content)
        
        return {"content": content, "urls": urls, "images": images}

    def get_chunk(self, text: str, start: int, limit: int) -> Dict[str, Any]:
        if not self.state.tokenizer:
            raise ValueError("Tokenizer not initialized")
            
        # Oblicz overhead
        overhead = (self.count_tokens(self.format_for_tokenization("")) - 
                   self.count_tokens(""))
        max_pos = len(text)
        
        # Wyszukiwanie binarne
        low, high = start, max_pos
        best_fit = start
        
        while low <= high:
            mid = (low + high) // 2
            candidate_text = text[start:mid]
            tokens = self.count_tokens(candidate_text) + overhead
            
            if tokens <= limit:
                best_fit = mid
                low = mid + 1
            else:
                high = mid - 1
                
        def try_adjust_boundary(pos: int) -> int:
            next_newline = text.find('\n', pos)
            if next_newline != -1 and next_newline < max_pos:
                candidate = next_newline + 1
                candidate_text = text[start:candidate]
                candidate_tokens = self.count_tokens(candidate_text) + overhead
                if candidate_tokens <= limit:
                    return candidate
                    
            prev_newline = text.rindex('\n', start, pos) if '\n' in text[start:pos] else -1
            if prev_newline > start:
                candidate = prev_newline + 1
                candidate_text = text[start:candidate]
                candidate_tokens = self.count_tokens(candidate_text) + overhead
                if candidate_tokens <= limit:
                    return candidate
                    
            return pos
            
        final_end = try_adjust_boundary(best_fit)
        final_text = text[start:final_end]
        
        return {"chunk_text": final_text, "chunk_end": final_end}

    async def split(self, text: str, limit: int, 
                   metadata_override: Optional[Dict[str, Any]] = None) -> List[Document]:
        if not text:
            raise ValueError("Text is required for splitting")
            
        await self.initialize_tokenizer()
        
        chunks: List[Document] = []
        position = 0
        current_headers: Dict[str, List[str]] = {}
        
        while position < len(text):
            chunk_result = self.get_chunk(text, position, limit)
            chunk_text = chunk_result["chunk_text"]
            chunk_end = chunk_result["chunk_end"]
            
            # Ekstrakcja nagłówków i URLi
            headers_in_chunk = self.extract_headers(chunk_text)
            current_headers = self.update_headers(current_headers, headers_in_chunk)
            
            url_data = self.extract_urls_and_images(chunk_text)
            
            # Tworzenie metadanych
            doc_uuid = str(uuid4())
            metadata = DocumentMetadata(
                uuid=doc_uuid,
                tokens=self.count_tokens(chunk_text),
                headers=current_headers,
                urls=url_data["urls"],
                images=url_data["images"],
                type=metadata_override.get("type", "text"),
                content_type=metadata_override.get("content_type", "chunk"),
                source_uuid=metadata_override.get("source_uuid", ""),
                conversation_uuid=metadata_override.get("conversation_uuid", "")
            )
            
            # Tworzenie dokumentu
            document = Document(
                uuid=doc_uuid,
                source_uuid=metadata_override.get("source_uuid", ""),
                conversation_uuid=metadata_override.get("conversation_uuid", ""),
                text=url_data["content"],
                metadata=metadata,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            
            chunks.append(document)
            position = chunk_end
            
        return chunks

# Przykład użycia:
async def example_usage():
    text_service = TextService()
    
    long_text = """
    # Główny Nagłówek
    
    To jest przykładowy tekst z [linkiem](https://example.com) i 
    ![obrazkiem](https://example.com/image.jpg).
    
    ## Podrozdział
    
    Więcej tekstu...
    """
    
    documents = await text_service.split(
        text=long_text,
        limit=1000,
        metadata_override={
            "type": "text",
            "content_type": "chunk",
            "source_uuid": "123",
            "conversation_uuid": "456"
        }
    )
    
    for doc in documents:
        print(f"Chunk UUID: {doc.uuid}")
        print(f"Tokens: {doc.metadata.tokens}")
        print(f"Headers: {doc.metadata.headers}")
        print(f"URLs: {doc.metadata.urls}")
        print(f"Images: {doc.metadata.images}")
        print("---")