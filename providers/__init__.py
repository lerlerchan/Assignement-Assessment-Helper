from .base_provider import BaseProvider, ProviderError
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider
from .lmstudio_provider import LMStudioProvider
from .generic_provider import GenericProvider

__all__ = [
    'BaseProvider',
    'ProviderError',
    'OpenAIProvider',
    'AnthropicProvider',
    'GeminiProvider',
    'OllamaProvider',
    'LMStudioProvider',
    'GenericProvider'
]


def get_provider(provider_name: str, config: dict) -> BaseProvider:
    """Factory function to get the appropriate provider."""
    providers = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'gemini': GeminiProvider,
        'ollama': OllamaProvider,
        'lmstudio': LMStudioProvider,
        'generic': GenericProvider
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ProviderError(f"Unknown provider: {provider_name}")

    return provider_class(config)
