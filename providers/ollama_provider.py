from typing import Dict, Any, Optional
import aiohttp
import json
from .base_provider import BaseProvider, ProviderError


class OllamaProvider(BaseProvider):
    """Ollama local AI provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = self.config.get('url', 'http://localhost:11434').rstrip('/')

    def _validate_config(self):
        # Ollama doesn't require API key, just URL
        pass

    @property
    def name(self) -> str:
        return "Ollama"

    @property
    def model(self) -> str:
        return self.config.get('model', 'llama2')

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response using Ollama API."""
        try:
            url = f"{self.base_url}/api/generate"

            payload = {
                'model': self.model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.3
                }
            }

            if system_prompt:
                payload['system'] = system_prompt

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=300)) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise ProviderError(f"Ollama API error: {response.status} - {text}")

                    result = await response.json()
                    return result.get('response', '')
        except aiohttp.ClientError as e:
            raise ProviderError(f"Ollama connection error: {str(e)}")
        except Exception as e:
            raise ProviderError(f"Ollama error: {str(e)}")

    async def test_connection(self) -> bool:
        """Test if the Ollama connection is working."""
        try:
            url = f"{self.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return response.status == 200
        except Exception:
            return False

    async def list_models(self) -> list:
        """List available models in Ollama."""
        try:
            url = f"{self.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return [m['name'] for m in result.get('models', [])]
        except Exception:
            pass
        return []
