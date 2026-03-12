"""Document models"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class Document(BaseModel):
    id: str
    content: str
    title: Optional[str] = None
    source: Optional[str] = None
    metadata: dict = {}
    created_at: datetime = datetime.now()
    chunks: List["DocumentChunk"] = []


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: dict = {}


class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float
    document: Optional[Document] = None
