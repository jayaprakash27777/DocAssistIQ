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


class BaselineEmbeddingProvider:
    """
    A mock baseline embedding provider that generates pseudo-random 
    (but deterministic-looking) vectors.
    In a real environment, this would integrate with OpenAI or a local model.
    """
    
    @property
    def model_name(self) -> str:
        return "text-embedding-3-small-mock"
        
    @property
    def dimensions(self) -> int:
        return 1536
        
    def _deterministic_mock_vector(self, text: str) -> List[float]:
        # Seed random to ensure the same text yields the same mock vector
        random.seed(hash(text))
        return [random.uniform(-1.0, 1.0) for _ in range(self.dimensions)]

    async def generate_embedding(self, text: str) -> List[float]:
        return self._deterministic_mock_vector(text)

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._deterministic_mock_vector(t) for t in texts]

# Singleton instance
_provider: EmbeddingProvider | None = None

def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is None:
        _provider = BaselineEmbeddingProvider()
    return _provider
