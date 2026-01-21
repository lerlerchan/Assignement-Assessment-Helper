from typing import Dict, Any, Optional
import aiohttp
import json
from .base_provider import BaseProvider, ProviderError


class LMStudioProvider(BaseProvider):
    """LM Studio local AI provider (OpenAI-compatible API)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = self.config.get('url', 'http://localhost:1234/v1').rstrip('/')

    def _validate_config(self):
        # LM Studio doesn't require API key
        pass

    @property
    def name(self) -> str:
        return "LM Studio"

    @property
    def model(self) -> str:
        return self.config.get('model', 'local-model')

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response using LM Studio's OpenAI-compatible API."""
        try:
            url = f"{self.base_url}/chat/completions"

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                'model': self.model,
                'messages': messages,
                'temperature': 0.3,
                'max_tokens': 4096
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=300)) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise ProviderError(f"LM Studio API error: {response.status} - {text}")

                    result = await response.json()
                    return result['choices'][0]['message']['content']
        except aiohttp.ClientError as e:
            raise ProviderError(f"LM Studio connection error: {str(e)}")
        except Exception as e:
            raise ProviderError(f"LM Studio error: {str(e)}")

    async def test_connection(self) -> bool:
        """Test if the LM Studio connection is working."""
        try:
            url = f"{self.base_url}/models"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return response.status == 200
        except Exception:
            return False

    async def list_models(self) -> list:
        """List available models in LM Studio."""
        try:
            url = f"{self.base_url}/models"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return [m['id'] for m in result.get('data', [])]
        except Exception:
            pass
        return []
