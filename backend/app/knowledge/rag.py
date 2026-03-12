"""RAG knowledge base"""

import uuid
import re
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime
from .document import Document, DocumentChunk, SearchResult
from .embeddings import EmbeddingEngine, EmbeddingConfig
from .vector_store import VectorStore


class KnowledgeBase:
    
    def __init__(
        self,
        storage_dir: str = "./data/knowledge",
        embedding_config: Optional[EmbeddingConfig] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir = self.storage_dir / "documents"
        self.documents_dir.mkdir(exist_ok=True)
        self.embedding_engine = EmbeddingEngine(embedding_config)
        self.vector_store = VectorStore(storage_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def upload_document(
        self,
        content: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Document:
        doc_id = str(uuid.uuid4())
        document = Document(
            id=doc_id,
            content=content,
            title=title,
            source=source,
            metadata=metadata or {}
        )
        chunks = self._split_document(document)
        document.chunks = chunks
        for chunk in chunks:
            chunk.embedding = self.embedding_engine.embed(chunk.content)
        self.vector_store.add(chunks)
        self._save_document(document)
        return document
    
    def upload_file(self, file_path: str) -> Document:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.upload_document(
            content=content,
            title=path.stem,
            source=str(path),
            metadata={"file_type": path.suffix}
        )
    
    def retrieve(self, query: str, top_k: int = 5) -> List[SearchResult]:
        query_vector = self.embedding_engine.embed(query)
        results = self.vector_store.search(query_vector, top_k)
        search_results = []
        for chunk, score in results:
            document = self._load_document(chunk.document_id)
            search_results.append(SearchResult(chunk=chunk, score=score, document=document))
        return search_results
    
    def get_context(self, query: str, top_k: int = 5, max_length: int = 2000) -> str:
        results = self.retrieve(query, top_k)
        context_parts = []
        current_length = 0
        for result in results:
            content = result.chunk.content
            if current_length + len(content) > max_length:
                break
            context_parts.append(f"[来源: {result.document.title or '未知'}]\n{content}")
            current_length += len(content)
        return "\n\n---\n\n".join(context_parts)
    
    def _split_document(self, document: Document) -> List[DocumentChunk]:
        content = document.content
        paragraphs = re.split(r'\n\s*\n', content)
        chunks = []
        current_chunk = ""
        chunk_index = 0
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunk_id = str(uuid.uuid4())
                    chunks.append(DocumentChunk(
                        id=chunk_id,
                        document_id=document.id,
                        content=current_chunk.strip(),
                        chunk_index=chunk_index
                    ))
                    chunk_index += 1
                current_chunk = para + "\n\n"
        if current_chunk.strip():
            chunk_id = str(uuid.uuid4())
            chunks.append(DocumentChunk(
                id=chunk_id,
                document_id=document.id,
                content=current_chunk.strip(),
                chunk_index=chunk_index
            ))
        return chunks
    
    def _save_document(self, document: Document) -> None:
        doc_file = self.documents_dir / f"{document.id}.json"
        import json
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(document.model_dump(), f, ensure_ascii=False, indent=2, default=str)
    
    def _load_document(self, doc_id: str) -> Optional[Document]:
        doc_file = self.documents_dir / f"{doc_id}.json"
        if not doc_file.exists():
            return None
        import json
        with open(doc_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Document(**data)
    
    def list_documents(self) -> List[Dict]:
        documents = []
        for doc_file in self.documents_dir.glob("*.json"):
            import json
            with open(doc_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                documents.append({
                    "id": data["id"],
                    "title": data.get("title"),
                    "source": data.get("source"),
                    "created_at": data.get("created_at"),
                    "chunk_count": len(data.get("chunks", []))
                })
        return documents
    
    def delete_document(self, doc_id: str) -> bool:
        document = self._load_document(doc_id)
        if not document:
            return False
        chunk_ids = [chunk.id for chunk in document.chunks]
        self.vector_store.delete(chunk_ids)
        doc_file = self.documents_dir / f"{doc_id}.json"
        if doc_file.exists():
            doc_file.unlink()
        return True
