from app.infrastructure.ai.interfaces import GenerationProvider, EmbeddingProvider
from app.infrastructure.ai.providers.baseline import BaselineGenerationProvider, BaselineEmbeddingProvider
from app.infrastructure.ai.providers.ollama_provider import OllamaGenerationProvider, OllamaEmbeddingProvider
from app.config import get_settings

_generation_provider: GenerationProvider | None = None
_embedding_provider: EmbeddingProvider | None = None

def get_generation_provider() -> GenerationProvider:
    global _generation_provider
    if _generation_provider is not None:
        return _generation_provider
        
    settings = get_settings()
    
    # Check if we should use local offline Ollama models
    # Defaulting to Ollama for offline/free use cases
    try:
        # Defaulting to llama3 or mistral based on user preference, "llama3" as default.
        _generation_provider = OllamaGenerationProvider(model_name="llama3")
    except Exception as e:
        # Fallback to Baseline if anything fails
        print(f"Warning: Failed to initialize Ollama: {e}")
        _generation_provider = BaselineGenerationProvider()
        
    return _generation_provider

def get_embedding_provider() -> EmbeddingProvider:
    global _embedding_provider
    if _embedding_provider is not None:
        return _embedding_provider
        
    try:
        # nomic-embed-text generates 768 dim embeddings
        _embedding_provider = OllamaEmbeddingProvider(model_name="nomic-embed-text", dimensions=768)
    except Exception as e:
        print(f"Warning: Failed to initialize Ollama Embeddings: {e}")
        _embedding_provider = BaselineEmbeddingProvider()
        
    return _embedding_provider
