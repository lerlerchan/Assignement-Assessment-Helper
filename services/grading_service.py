import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

from models import Student, Rubric, RubricElement, GradeResult, ElementGrade
from services.pdf_service import PDFService
from services.ai_service import AIService


class GradingSession:
    """Represents a grading session with all its state."""

    def __init__(self, session_id: str = None):
        self.id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.students: List[Student] = []
        self.rubric: Optional[Rubric] = None
        self.results: List[GradeResult] = []
        self.status = 'created'  # created, processing, completed, error
        self.current_index = 0
        self.error_message = ''

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'students': [s.to_dict() for s in self.students],
            'rubric': self.rubric.to_dict() if self.rubric else None,
            'results': [r.to_dict() for r in self.results],
            'status': self.status,
            'current_index': self.current_index,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GradingSession':
        session = cls(session_id=data.get('id'))
        session.created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        session.students = [Student.from_dict(s) for s in data.get('students', [])]
        session.rubric = Rubric.from_dict(data['rubric']) if data.get('rubric') else None
        session.results = [GradeResult.from_dict(r) for r in data.get('results', [])]
        session.status = data.get('status', 'created')
        session.current_index = data.get('current_index', 0)
        session.error_message = data.get('error_message', '')
        return session


class GradingService:
    """Service for managing the grading workflow."""

    def __init__(self):
        self.pdf_service = PDFService()
        self.ai_service = AIService()
        self._sessions: Dict[str, GradingSession] = {}

    def create_session(self) -> GradingSession:
        """Create a new grading session."""
        session = GradingSession()
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[GradingSession]:
        """Get a grading session by ID."""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str):
        """Delete a grading session."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def load_students_from_pdfs(self, session_id: str, pdf_paths: List[str],
                                is_combined: bool = False,
                                pages_per_student: int = None,
                                student_id_pattern: str = None) -> List[Student]:
        """
        Load students from PDF files.

        Args:
            session_id: The session to add students to
            pdf_paths: List of PDF file paths
            is_combined: True if it's a single combined PDF with all students
            pages_per_student: For combined PDF, pages per student
            student_id_pattern: Regex pattern to identify student sections
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if is_combined and len(pdf_paths) == 1:
            students = self.pdf_service.extract_students_from_combined(
                pdf_paths[0],
                pages_per_student=pages_per_student,
                student_id_pattern=student_id_pattern
            )
        else:
            students = self.pdf_service.extract_from_individual_pdfs(pdf_paths)

        session.students = students
        return students

    def load_rubric(self, session_id: str, rubric_source: str,
                    source_type: str = 'text') -> Rubric:
        """
        Load a rubric for the session.

        Args:
            session_id: The session ID
            rubric_source: Either text content or PDF path
            source_type: 'text' or 'pdf'
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if source_type == 'pdf':
            rubric_text = self.pdf_service.extract_text(rubric_source)
            rubric = Rubric.from_text(rubric_text, name="Uploaded Rubric")
            rubric.source = 'pdf'
        else:
            rubric = Rubric.from_text(rubric_source, name="Custom Rubric")
            rubric.source = 'text'

        session.rubric = rubric
        return rubric

    async def parse_rubric_with_ai(self, session_id: str) -> Rubric:
        """Use AI to parse the rubric into structured format."""
        session = self.get_session(session_id)
        if not session or not session.rubric:
            raise ValueError("Session or rubric not found")

        parsed = await self.ai_service.parse_rubric(session.rubric.raw_text)

        # Update rubric with parsed data
        session.rubric.name = parsed.get('name', session.rubric.name)
        session.rubric.total_marks = parsed.get('total_marks', session.rubric.total_marks)

        for criterion in parsed.get('criteria', []):
            element = RubricElement(
                name=criterion.get('name', ''),
                description=criterion.get('description', ''),
                max_marks=float(criterion.get('max_marks', 0))
            )
            session.rubric.add_element(element)

        return session.rubric

    async def grade_all(self, session_id: str,
                        progress_callback: Callable[[int, int, str], None] = None) -> List[GradeResult]:
        """
        Grade all students in the session.

        Args:
            session_id: The session ID
            progress_callback: Optional callback(current, total, student_id)
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if not session.students:
            raise ValueError("No students loaded")

        if not session.rubric:
            raise ValueError("No rubric loaded")

        session.status = 'processing'
        session.results = []

        rubric_text = session.rubric.get_grading_prompt()
        total = len(session.students)

        for i, student in enumerate(session.students):
            session.current_index = i

            if progress_callback:
                progress_callback(i, total, student.id)

            try:
                ai_result = await self.ai_service.grade_assignment(
                    student_content=student.content,
                    rubric_text=rubric_text
                )

                # Convert AI result to GradeResult
                grade_result = self._convert_ai_result(student, ai_result, session.rubric)
                session.results.append(grade_result)

            except Exception as e:
                # Create error result
                error_result = GradeResult(
                    student_id=student.id,
                    student_name=student.name,
                    overall_feedback=f"Error during grading: {str(e)}",
                    ai_provider="Error"
                )
                session.results.append(error_result)

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        session.status = 'completed'
        session.current_index = total

        if progress_callback:
            progress_callback(total, total, 'Complete')

        return session.results

    def _convert_ai_result(self, student: Student, ai_result: dict,
                           rubric: Rubric) -> GradeResult:
        """Convert AI grading result to GradeResult model."""
        from utils.config_manager import get_config
        config = get_config()

        grade_result = GradeResult(
            student_id=ai_result.get('student_id', student.id),
            student_name=ai_result.get('student_name', student.name),
            overall_feedback=ai_result.get('overall_feedback', ''),
            ai_provider=ai_result.get('ai_provider', ''),
            is_suggestion_only=config.get('marking_mode') == 'suggestions'
        )

        # Add element grades
        for grade_data in ai_result.get('grades', []):
            element_grade = ElementGrade(
                element_name=grade_data.get('criterion', ''),
                marks_awarded=float(grade_data.get('marks', 0)),
                max_marks=float(grade_data.get('max_marks', 0)),
                feedback=grade_data.get('feedback', '')
            )
            grade_result.add_element_grade(element_grade)

        return grade_result

    def update_grade(self, session_id: str, student_id: str,
                     element_name: str = None, marks: float = None,
                     overall_feedback: str = None) -> bool:
        """Update a grade for a student (for review/editing)."""
        session = self.get_session(session_id)
        if not session:
            return False

        for result in session.results:
            if result.student_id == student_id:
                if element_name and marks is not None:
                    result.update_element_grade(element_name, marks)
                if overall_feedback is not None:
                    result.overall_feedback = overall_feedback
                    result.manually_edited = True
                return True

        return False

    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """Get current progress of grading session."""
        session = self.get_session(session_id)
        if not session:
            return {'error': 'Session not found'}

        return {
            'session_id': session.id,
            'status': session.status,
            'total_students': len(session.students),
            'completed': len(session.results),
            'current_index': session.current_index,
            'error_message': session.error_message
        }

    def save_session(self, session_id: str, filepath: str):
        """Save session to file."""
        session = self.get_session(session_id)
        if session:
            with open(filepath, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)

    def load_session(self, filepath: str) -> GradingSession:
        """Load session from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        session = GradingSession.from_dict(data)
        self._sessions[session.id] = session
        return session
