from typing import Dict, Any, Optional
import aiohttp
import json
from .base_provider import BaseProvider, ProviderError


class GenericProvider(BaseProvider):
    """Generic OpenAI-compatible API provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = self.config.get('url', '').rstrip('/')
        self.api_key = self.config.get('api_key', '')

    def _validate_config(self):
        if not self.config.get('url'):
            raise ProviderError("API URL is required for generic provider")

    @property
    def name(self) -> str:
        return "Generic OpenAI-compatible"

    @property
    def model(self) -> str:
        return self.config.get('model', 'default')

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response using a generic OpenAI-compatible API."""
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

            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise ProviderError(f"API error: {response.status} - {text}")

                    result = await response.json()
                    return result['choices'][0]['message']['content']
        except aiohttp.ClientError as e:
            raise ProviderError(f"Connection error: {str(e)}")
        except KeyError as e:
            raise ProviderError(f"Unexpected API response format: {str(e)}")
        except Exception as e:
            raise ProviderError(f"Error: {str(e)}")

    async def test_connection(self) -> bool:
        """Test if the connection is working."""
        try:
            url = f"{self.base_url}/models"
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    # Some endpoints may not have /models, so try a simple completion
                    if response.status == 200:
                        return True

            # Fallback: try a minimal completion
            messages = [{"role": "user", "content": "Hi"}]
            payload = {
                'model': self.model,
                'messages': messages,
                'max_tokens': 5
            }
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
