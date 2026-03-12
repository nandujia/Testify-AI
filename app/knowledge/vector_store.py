"""Vector store"""

import json
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from .document import DocumentChunk


class VectorStore:
    
    def __init__(self, storage_dir: str = "./data/knowledge"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"
        self.vectors_file = self.storage_dir / "vectors.npy"
        self.chunks: Dict[str, DocumentChunk] = {}
        self.vectors: Optional[np.ndarray] = None
        self._load()
    
    def _load(self) -> None:
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for chunk_id, chunk_data in data.get("chunks", {}).items():
                    self.chunks[chunk_id] = DocumentChunk(**chunk_data)
        if self.vectors_file.exists():
            self.vectors = np.load(str(self.vectors_file))
    
    def _save(self) -> None:
        data = {"chunks": {chunk_id: chunk.model_dump() for chunk_id, chunk in self.chunks.items()}}
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        if self.vectors is not None:
            np.save(str(self.vectors_file), self.vectors)
    
    def add(self, chunks: List[DocumentChunk]) -> None:
        for chunk in chunks:
            if chunk.embedding is None:
                continue
            self.chunks[chunk.id] = chunk
            if self.vectors is None:
                self.vectors = np.array([chunk.embedding])
            else:
                self.vectors = np.vstack([self.vectors, chunk.embedding])
        self._save()
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        if self.vectors is None or len(self.chunks) == 0:
            return []
        query = np.array(query_vector)
        norms = np.linalg.norm(self.vectors, axis=1)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []
        similarities = np.dot(self.vectors, query) / (norms * query_norm)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = []
        chunk_list = list(self.chunks.values())
        for idx in top_indices:
            if idx < len(chunk_list):
                results.append((chunk_list[idx], float(similarities[idx])))
        return results
    
    def delete(self, chunk_ids: List[str]) -> None:
        for chunk_id in chunk_ids:
            if chunk_id in self.chunks:
                del self.chunks[chunk_id]
        if self.chunks:
            embeddings = [chunk.embedding for chunk in self.chunks.values() if chunk.embedding is not None]
            if embeddings:
                self.vectors = np.array(embeddings)
            else:
                self.vectors = None
        else:
            self.vectors = None
        self._save()
    
    def clear(self) -> None:
        self.chunks = {}
        self.vectors = None
        self._save()
    
    def count(self) -> int:
        return len(self.chunks)
