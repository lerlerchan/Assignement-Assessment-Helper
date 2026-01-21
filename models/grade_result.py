from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class ElementGrade:
    """Grade for a single rubric element."""

    element_name: str
    marks_awarded: float
    max_marks: float
    feedback: str = ""

    @property
    def percentage(self) -> float:
        if self.max_marks == 0:
            return 0.0
        return (self.marks_awarded / self.max_marks) * 100

    def to_dict(self) -> dict:
        return {
            'element_name': self.element_name,
            'marks_awarded': self.marks_awarded,
            'max_marks': self.max_marks,
            'feedback': self.feedback,
            'percentage': self.percentage
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ElementGrade':
        return cls(
            element_name=data.get('element_name', ''),
            marks_awarded=float(data.get('marks_awarded', 0)),
            max_marks=float(data.get('max_marks', 0)),
            feedback=data.get('feedback', '')
        )


@dataclass
class GradeResult:
    """Complete grading result for a student."""

    student_id: str
    student_name: str
    element_grades: List[ElementGrade] = field(default_factory=list)
    overall_feedback: str = ""
    graded_at: Optional[datetime] = None
    ai_provider: str = ""
    is_suggestion_only: bool = False
    manually_edited: bool = False

    def __post_init__(self):
        if self.graded_at is None:
            self.graded_at = datetime.now()

    @property
    def total_marks(self) -> float:
        return sum(g.marks_awarded for g in self.element_grades)

    @property
    def max_total_marks(self) -> float:
        return sum(g.max_marks for g in self.element_grades)

    @property
    def percentage(self) -> float:
        if self.max_total_marks == 0:
            return 0.0
        return (self.total_marks / self.max_total_marks) * 100

    def add_element_grade(self, grade: ElementGrade):
        self.element_grades.append(grade)

    def update_element_grade(self, element_name: str, marks: float, feedback: str = None):
        """Update a specific element grade."""
        for grade in self.element_grades:
            if grade.element_name == element_name:
                grade.marks_awarded = marks
                if feedback is not None:
                    grade.feedback = feedback
                self.manually_edited = True
                break

    def to_dict(self) -> dict:
        return {
            'student_id': self.student_id,
            'student_name': self.student_name,
            'element_grades': [g.to_dict() for g in self.element_grades],
            'overall_feedback': self.overall_feedback,
            'graded_at': self.graded_at.isoformat() if self.graded_at else None,
            'ai_provider': self.ai_provider,
            'total_marks': self.total_marks,
            'max_total_marks': self.max_total_marks,
            'percentage': self.percentage,
            'is_suggestion_only': self.is_suggestion_only,
            'manually_edited': self.manually_edited
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GradeResult':
        result = cls(
            student_id=data.get('student_id', ''),
            student_name=data.get('student_name', ''),
            overall_feedback=data.get('overall_feedback', ''),
            graded_at=datetime.fromisoformat(data['graded_at']) if data.get('graded_at') else None,
            ai_provider=data.get('ai_provider', ''),
            is_suggestion_only=data.get('is_suggestion_only', False),
            manually_edited=data.get('manually_edited', False)
        )
        for grade_data in data.get('element_grades', []):
            result.add_element_grade(ElementGrade.from_dict(grade_data))
        return result
