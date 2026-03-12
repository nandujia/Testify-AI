"""Embedding engine"""

from typing import List, Optional
import hashlib
import httpx
from pydantic import BaseModel


class EmbeddingConfig(BaseModel):
    provider: str = "local"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "text-embedding-ada-002"
    dimension: int = 1536


class EmbeddingEngine:
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
    
    def embed(self, text: str) -> List[float]:
        if self.config.provider == "local":
            return self._local_embed(text)
        elif self.config.provider == "openai":
            return self._openai_embed(text)
        else:
            return self._local_embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(text) for text in texts]
    
    def _local_embed(self, text: str) -> List[float]:
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        vector = []
        for i in range(min(len(hash_bytes) * 8, self.config.dimension)):
            byte_idx = i // 8
            bit_idx = i % 8
            if byte_idx < len(hash_bytes):
                bit_val = (hash_bytes[byte_idx] >> bit_idx) & 1
                vector.append(float(bit_val))
            else:
                vector.append(0.0)
        while len(vector) < self.config.dimension:
            vector = vector + vector[:self.config.dimension - len(vector)]
        return vector[:self.config.dimension]
    
    def _openai_embed(self, text: str) -> List[float]:
        if not self.config.api_key:
            return self._local_embed(text)
        url = self.config.base_url or "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.config.model, "input": text}
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
        return result["data"][0]["embedding"]
