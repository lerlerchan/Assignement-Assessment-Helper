from typing import Dict, Any, Optional
from .base_provider import BaseProvider, ProviderError

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if OPENAI_AVAILABLE:
            self.client = AsyncOpenAI(api_key=self.config.get('api_key'))
        else:
            self.client = None

    def _validate_config(self):
        if not OPENAI_AVAILABLE:
            raise ProviderError("OpenAI library not installed. Run: pip install openai")
        if not self.config.get('api_key'):
            raise ProviderError("OpenAI API key is required")

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def model(self) -> str:
        return self.config.get('model', 'gpt-4o')

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response using OpenAI API."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Lower temperature for consistent grading
                max_tokens=4096
            )

            return response.choices[0].message.content
        except Exception as e:
            raise ProviderError(f"OpenAI API error: {str(e)}")

    async def test_connection(self) -> bool:
        """Test if the OpenAI connection is working."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False
