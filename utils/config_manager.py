import os
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class ConfigManager:
    """Manages application configuration with encrypted API key storage."""

    CONFIG_DIR = Path.home() / '.grading_assistant'
    CONFIG_FILE = CONFIG_DIR / 'config.json'
    KEY_FILE = CONFIG_DIR / '.key'

    DEFAULT_CONFIG = {
        'ai_provider': 'openai',
        'openai_api_key': '',
        'anthropic_api_key': '',
        'gemini_api_key': '',
        'ollama_url': 'http://localhost:11434',
        'ollama_model': 'llama2',
        'lmstudio_url': 'http://localhost:1234/v1',
        'lmstudio_model': 'local-model',
        'generic_url': '',
        'generic_api_key': '',
        'generic_model': '',
        'marking_mode': 'auto',  # 'auto' or 'suggestions'
        'feedback_style': 'detailed',  # 'brief' or 'detailed'
        'theme': 'light',
        'auto_save': True,
        'default_total_marks': 100
    }

    SENSITIVE_KEYS = [
        'openai_api_key', 'anthropic_api_key', 'gemini_api_key',
        'generic_api_key', 'lmstudio_api_key'
    ]

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._fernet: Optional[Fernet] = None
        self._ensure_config_dir()
        self._init_encryption()
        self._load_config()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _init_encryption(self):
        """Initialize encryption using a machine-specific key."""
        if self.KEY_FILE.exists():
            key = self.KEY_FILE.read_bytes()
        else:
            # Generate a new key
            key = Fernet.generate_key()
            self.KEY_FILE.write_bytes(key)
            # Make the key file read-only for the user
            try:
                os.chmod(self.KEY_FILE, 0o600)
            except:
                pass  # Windows may not support chmod

        self._fernet = Fernet(key)

    def _encrypt(self, value: str) -> str:
        """Encrypt a string value."""
        if not value:
            return ''
        return self._fernet.encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        """Decrypt an encrypted string value."""
        if not value:
            return ''
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except Exception:
            return ''

    def _load_config(self):
        """Load configuration from file."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    saved_config = json.load(f)

                # Merge with defaults to ensure all keys exist
                self._config = {**self.DEFAULT_CONFIG, **saved_config}

                # Decrypt sensitive values
                for key in self.SENSITIVE_KEYS:
                    if key in self._config and self._config[key]:
                        self._config[key] = self._decrypt(self._config[key])
            except Exception as e:
                print(f"Error loading config: {e}")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()

    def _save_config(self):
        """Save configuration to file."""
        # Create a copy for saving with encrypted sensitive values
        save_config = self._config.copy()

        for key in self.SENSITIVE_KEYS:
            if key in save_config and save_config[key]:
                save_config[key] = self._encrypt(save_config[key])

        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(save_config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self._config[key] = value
        self._save_config()

    def update(self, values: Dict[str, Any]):
        """Update multiple configuration values."""
        self._config.update(values)
        self._save_config()

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values (with sensitive values masked)."""
        result = self._config.copy()
        for key in self.SENSITIVE_KEYS:
            if key in result and result[key]:
                result[key] = '***' + result[key][-4:] if len(result[key]) > 4 else '****'
        return result

    def get_all_raw(self) -> Dict[str, Any]:
        """Get all configuration values (unmasked - use with caution)."""
        return self._config.copy()

    def has_api_key(self, provider: str) -> bool:
        """Check if an API key is configured for a provider."""
        key_map = {
            'openai': 'openai_api_key',
            'anthropic': 'anthropic_api_key',
            'gemini': 'gemini_api_key',
            'generic': 'generic_api_key'
        }
        key_name = key_map.get(provider)
        if key_name:
            return bool(self._config.get(key_name))
        # Ollama and LM Studio don't need API keys
        return provider in ['ollama', 'lmstudio']

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific AI provider."""
        configs = {
            'openai': {
                'api_key': self.get('openai_api_key'),
                'model': self.get('openai_model', 'gpt-4o')
            },
            'anthropic': {
                'api_key': self.get('anthropic_api_key'),
                'model': self.get('anthropic_model', 'claude-sonnet-4-20250514')
            },
            'gemini': {
                'api_key': self.get('gemini_api_key'),
                'model': self.get('gemini_model', 'gemini-pro')
            },
            'ollama': {
                'url': self.get('ollama_url', 'http://localhost:11434'),
                'model': self.get('ollama_model', 'llama2')
            },
            'lmstudio': {
                'url': self.get('lmstudio_url', 'http://localhost:1234/v1'),
                'model': self.get('lmstudio_model', 'local-model')
            },
            'generic': {
                'url': self.get('generic_url'),
                'api_key': self.get('generic_api_key'),
                'model': self.get('generic_model')
            }
        }
        return configs.get(provider, {})

    def reset(self):
        """Reset configuration to defaults."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_config()


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
