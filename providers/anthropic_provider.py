from typing import Dict, Any, Optional
from .base_provider import BaseProvider, ProviderError

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if ANTHROPIC_AVAILABLE:
            self.client = anthropic.AsyncAnthropic(api_key=self.config.get('api_key'))
        else:
            self.client = None

    def _validate_config(self):
        if not ANTHROPIC_AVAILABLE:
            raise ProviderError("Anthropic library not installed. Run: pip install anthropic")
        if not self.config.get('api_key'):
            raise ProviderError("Anthropic API key is required")

    @property
    def name(self) -> str:
        return "Anthropic Claude"

    @property
    def model(self) -> str:
        return self.config.get('model', 'claude-sonnet-4-20250514')

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response using Anthropic API."""
        try:
            kwargs = {
                'model': self.model,
                'max_tokens': 4096,
                'messages': [{"role": "user", "content": prompt}]
            }

            if system_prompt:
                kwargs['system'] = system_prompt

            response = await self.client.messages.create(**kwargs)

            return response.content[0].text
        except Exception as e:
            raise ProviderError(f"Anthropic API error: {str(e)}")

    async def test_connection(self) -> bool:
        """Test if the Anthropic connection is working."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except Exception:
            return False
