from typing import Dict, Any, Optional
import asyncio
from .base_provider import BaseProvider, ProviderError

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiProvider(BaseProvider):
    """Google Gemini API provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if GEMINI_AVAILABLE:
            genai.configure(api_key=self.config.get('api_key'))
            self._model = genai.GenerativeModel(self.model)
        else:
            self._model = None

    def _validate_config(self):
        if not GEMINI_AVAILABLE:
            raise ProviderError("Google Generative AI library not installed. Run: pip install google-generativeai")
        if not self.config.get('api_key'):
            raise ProviderError("Gemini API key is required")

    @property
    def name(self) -> str:
        return "Google Gemini"

    @property
    def model(self) -> str:
        return self.config.get('model', 'gemini-pro')

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response using Gemini API."""
        try:
            # Combine system prompt with user prompt for Gemini
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Gemini's generate_content is not async, so we run it in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=4096
                    )
                )
            )

            return response.text
        except Exception as e:
            raise ProviderError(f"Gemini API error: {str(e)}")

    async def test_connection(self) -> bool:
        """Test if the Gemini connection is working."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._model.generate_content("Hello")
            )
            return True
        except Exception:
            return False
