from typing import Dict, Any, Optional, List
import asyncio

from providers import get_provider, BaseProvider, ProviderError
from utils.config_manager import get_config


class AIService:
    """Service for managing AI provider interactions."""

    def __init__(self):
        self.config = get_config()
        self._provider: Optional[BaseProvider] = None

    def get_provider(self, provider_name: str = None) -> BaseProvider:
        """Get the configured AI provider."""
        if provider_name is None:
            provider_name = self.config.get('ai_provider', 'openai')

        provider_config = self.config.get_provider_config(provider_name)
        return get_provider(provider_name, provider_config)

    async def test_provider(self, provider_name: str = None) -> Dict[str, Any]:
        """Test connection to a provider."""
        try:
            provider = self.get_provider(provider_name)
            success = await provider.test_connection()
            return {
                'success': success,
                'provider': provider.name,
                'message': 'Connection successful' if success else 'Connection failed'
            }
        except ProviderError as e:
            return {
                'success': False,
                'provider': provider_name,
                'message': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'provider': provider_name,
                'message': f'Unexpected error: {str(e)}'
            }

    async def grade_assignment(self, student_content: str, rubric_text: str,
                               provider_name: str = None) -> Dict[str, Any]:
        """Grade a single assignment."""
        provider = self.get_provider(provider_name)

        auto_calculate = self.config.get('marking_mode') == 'auto'
        detailed_feedback = self.config.get('feedback_style') == 'detailed'

        return await provider.grade_assignment(
            student_content=student_content,
            rubric_text=rubric_text,
            auto_calculate=auto_calculate,
            detailed_feedback=detailed_feedback
        )

    async def extract_student_info(self, content: str,
                                   provider_name: str = None) -> Dict[str, str]:
        """Extract student information from content."""
        provider = self.get_provider(provider_name)
        return await provider.extract_student_info(content)

    async def parse_rubric(self, rubric_text: str,
                           provider_name: str = None) -> Dict[str, Any]:
        """Parse a rubric into structured format."""
        provider = self.get_provider(provider_name)
        return await provider.parse_rubric(rubric_text)

    async def batch_grade(self, assignments: List[Dict[str, str]], rubric_text: str,
                          provider_name: str = None,
                          progress_callback=None) -> List[Dict[str, Any]]:
        """
        Grade multiple assignments.

        Args:
            assignments: List of dicts with 'content', 'student_id', 'student_name'
            rubric_text: The rubric text
            provider_name: Optional provider override
            progress_callback: Optional callback(current, total, student_id)

        Returns:
            List of grading results
        """
        results = []
        total = len(assignments)

        for i, assignment in enumerate(assignments):
            student_id = assignment.get('student_id', f'Student_{i+1}')

            if progress_callback:
                progress_callback(i, total, student_id)

            try:
                result = await self.grade_assignment(
                    student_content=assignment['content'],
                    rubric_text=rubric_text,
                    provider_name=provider_name
                )

                # Ensure student info is present
                if not result.get('student_id') or result.get('student_id') == 'Unknown':
                    result['student_id'] = student_id
                if not result.get('student_name') or result.get('student_name') == 'Unknown':
                    result['student_name'] = assignment.get('student_name', 'Unknown')

                result['success'] = True
                results.append(result)

            except Exception as e:
                results.append({
                    'student_id': student_id,
                    'student_name': assignment.get('student_name', 'Unknown'),
                    'success': False,
                    'error': str(e)
                })

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        if progress_callback:
            progress_callback(total, total, 'Complete')

        return results

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers with their configuration status."""
        providers = [
            {
                'id': 'openai',
                'name': 'OpenAI',
                'configured': self.config.has_api_key('openai'),
                'requires_key': True
            },
            {
                'id': 'anthropic',
                'name': 'Anthropic Claude',
                'configured': self.config.has_api_key('anthropic'),
                'requires_key': True
            },
            {
                'id': 'gemini',
                'name': 'Google Gemini',
                'configured': self.config.has_api_key('gemini'),
                'requires_key': True
            },
            {
                'id': 'ollama',
                'name': 'Ollama (Local)',
                'configured': True,  # Ollama doesn't need API key
                'requires_key': False
            },
            {
                'id': 'lmstudio',
                'name': 'LM Studio (Local)',
                'configured': True,
                'requires_key': False
            },
            {
                'id': 'generic',
                'name': 'Generic OpenAI-compatible',
                'configured': bool(self.config.get('generic_url')),
                'requires_key': False
            }
        ]
        return providers

    async def list_local_models(self, provider_name: str) -> List[str]:
        """List available models for local providers."""
        try:
            provider = self.get_provider(provider_name)
            if hasattr(provider, 'list_models'):
                return await provider.list_models()
        except Exception:
            pass
        return []
