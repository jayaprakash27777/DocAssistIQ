import random
from typing import List, Protocol

class EmbeddingProvider(Protocol):
    """
    Protocol for generating vector embeddings from text.
    """
    @property
    def model_name(self) -> str:
        """Return the canonical name of the embedding model being used."""
        ...

    @property
    def dimensions(self) -> int:
        """Return the dimensionality of the generated embeddings."""
        ...

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate a single embedding vector for the given text."""
        ...

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of texts."""
        ...


import httpx

class OllamaEmbeddingProvider:
    """
    Real embedding provider using local Ollama model (nomic-embed-text).
    """
    
    @property
    def model_name(self) -> str:
        return "nomic-embed-text"
        
    @property
    def dimensions(self) -> int:
        return 768
        
    async def generate_embedding(self, text: str) -> List[float]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:11434/api/embeddings",
                json={"model": self.model_name, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        # For simplicity, we process them sequentially or concurrently.
        # Ollama supports sequential requests.
        embeddings = []
        for text in texts:
            emb = await self.generate_embedding(text)
            embeddings.append(emb)
        return embeddings

# Singleton instance
_provider: EmbeddingProvider | None = None

def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is None:
        _provider = OllamaEmbeddingProvider()
    return _provider
