import httpx
import json
import structlog
from typing import Dict, Any, List

log = structlog.get_logger(__name__)

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
        # Using the model the user installed, prioritize llama3.2 but fallback to qwen
        self.default_model = "llama3.2" 

    async def generate(self, prompt: str, system: str = "", model: str = None) -> str:
        """Simple text generation using Ollama."""
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "system": system,
            "stream": False
        }
        
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            log.error("ollama_generate_failed", error=str(e))
            raise e

    async def generate_json(self, prompt: str, system: str = "", model: str = None) -> Dict[str, Any]:
        """Generate guaranteed JSON output using Ollama's format=json parameter."""
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": "json"
        }
        
        try:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return json.loads(data.get("response", "{}"))
        except Exception as e:
            log.error("ollama_generate_json_failed", error=str(e))
            raise e

llm_service = OllamaService()
