from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RubricElement:
    """A single element/criterion in a rubric."""

    name: str
    description: str
    max_marks: float
    weight: float = 1.0

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'max_marks': self.max_marks,
            'weight': self.weight
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RubricElement':
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            max_marks=float(data.get('max_marks', 0)),
            weight=float(data.get('weight', 1.0))
        )


@dataclass
class Rubric:
    """Represents a grading rubric with multiple elements."""

    name: str
    elements: List[RubricElement] = field(default_factory=list)
    total_marks: float = 100.0
    source: str = ""  # 'pdf' or 'text'
    raw_text: str = ""

    @property
    def calculated_total(self) -> float:
        """Calculate total marks from elements."""
        return sum(e.max_marks for e in self.elements)

    def add_element(self, element: RubricElement):
        self.elements.append(element)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'elements': [e.to_dict() for e in self.elements],
            'total_marks': self.total_marks,
            'source': self.source,
            'raw_text': self.raw_text
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Rubric':
        rubric = cls(
            name=data.get('name', 'Rubric'),
            total_marks=float(data.get('total_marks', 100)),
            source=data.get('source', ''),
            raw_text=data.get('raw_text', '')
        )
        for elem_data in data.get('elements', []):
            rubric.add_element(RubricElement.from_dict(elem_data))
        return rubric

    @classmethod
    def from_text(cls, text: str, name: str = "Custom Rubric") -> 'Rubric':
        """Create a rubric from raw text - AI will parse this later."""
        return cls(
            name=name,
            source='text',
            raw_text=text
        )

    def get_grading_prompt(self) -> str:
        """Generate a prompt-friendly version of the rubric."""
        if self.elements:
            lines = [f"Rubric: {self.name}", f"Total Marks: {self.total_marks}", ""]
            lines.append("Criteria:")
            for i, elem in enumerate(self.elements, 1):
                lines.append(f"{i}. {elem.name} ({elem.max_marks} marks)")
                lines.append(f"   {elem.description}")
            return "\n".join(lines)
        elif self.raw_text:
            return f"Rubric: {self.name}\n\n{self.raw_text}"
        else:
            return "No rubric provided. Use general academic standards."
