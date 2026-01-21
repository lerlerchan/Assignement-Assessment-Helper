from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
import re


class ProviderError(Exception):
    """Exception raised by AI providers."""
    pass


class BaseProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self):
        """Validate provider-specific configuration."""
        pass

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from the AI model."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the provider connection is working."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass

    def get_grading_system_prompt(self, detailed: bool = True) -> str:
        """Get the system prompt for grading."""
        style = "detailed" if detailed else "brief"

        return f"""You are an expert academic grader. Your task is to evaluate student assignments based on a provided rubric.

Instructions:
1. Carefully read the student's work
2. Evaluate against each rubric criterion
3. Provide {style} feedback for each criterion
4. Be fair, constructive, and educational in your feedback
5. Focus on specific examples from the student's work

Output Format:
You MUST respond in valid JSON format with this structure:
{{
    "student_id": "extracted or inferred student ID",
    "student_name": "extracted or inferred student name",
    "grades": [
        {{
            "criterion": "criterion name",
            "marks": <number>,
            "max_marks": <number>,
            "feedback": "specific feedback for this criterion"
        }}
    ],
    "overall_feedback": "summary feedback",
    "strengths": ["strength 1", "strength 2"],
    "areas_for_improvement": ["area 1", "area 2"]
}}

Important:
- Extract student ID/name from the document if present (look for headers, title pages, etc.)
- If not found, use "Unknown" for ID and infer from content if possible
- Marks must be numbers within the max_marks limit
- Provide constructive, educational feedback
- Be consistent in grading standards"""

    def build_grading_prompt(self, student_content: str, rubric_text: str,
                             auto_calculate: bool = True) -> str:
        """Build the prompt for grading a student's work."""
        mode = "Calculate exact marks" if auto_calculate else "Suggest marks (teacher will finalize)"

        return f"""Grade the following student assignment based on the rubric.

Mode: {mode}

=== RUBRIC ===
{rubric_text}

=== STUDENT WORK ===
{student_content}

=== END OF STUDENT WORK ===

Please grade this work and respond in the JSON format specified."""

    def parse_grading_response(self, response: str) -> Dict[str, Any]:
        """Parse the AI's grading response into a structured format."""
        # Try to extract JSON from the response
        try:
            # First, try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # If all else fails, return a basic structure
        return {
            'student_id': 'Unknown',
            'student_name': 'Unknown',
            'grades': [],
            'overall_feedback': response,
            'parse_error': True
        }

    async def grade_assignment(self, student_content: str, rubric_text: str,
                               auto_calculate: bool = True,
                               detailed_feedback: bool = True) -> Dict[str, Any]:
        """Grade a student assignment."""
        system_prompt = self.get_grading_system_prompt(detailed=detailed_feedback)
        user_prompt = self.build_grading_prompt(student_content, rubric_text, auto_calculate)

        try:
            response = await self.generate(user_prompt, system_prompt)
            result = self.parse_grading_response(response)
            result['ai_provider'] = self.name
            return result
        except Exception as e:
            raise ProviderError(f"Grading failed: {str(e)}")

    async def extract_student_info(self, content: str) -> Dict[str, str]:
        """Extract student ID and name from content."""
        prompt = """Extract the student ID and name from the following document.
Look for:
- Student ID numbers (usually alphanumeric)
- Names (in headers, title pages, or body)
- Roll numbers or registration numbers

Respond in JSON format:
{"student_id": "extracted ID or Unknown", "student_name": "extracted name or Unknown"}

Document:
""" + content[:2000]  # Limit to first 2000 chars for efficiency

        try:
            response = await self.generate(prompt)
            return self.parse_grading_response(response)
        except Exception:
            return {'student_id': 'Unknown', 'student_name': 'Unknown'}

    async def parse_rubric(self, rubric_text: str) -> Dict[str, Any]:
        """Parse a rubric text into structured format."""
        prompt = """Parse the following rubric into structured criteria.
For each criterion, extract:
- Name
- Description
- Maximum marks

Respond in JSON format:
{
    "name": "rubric name",
    "total_marks": <number>,
    "criteria": [
        {"name": "criterion name", "description": "what it evaluates", "max_marks": <number>}
    ]
}

Rubric:
""" + rubric_text

        try:
            response = await self.generate(prompt)
            return self.parse_grading_response(response)
        except Exception:
            return {
                'name': 'Custom Rubric',
                'total_marks': 100,
                'criteria': [],
                'parse_error': True
            }
