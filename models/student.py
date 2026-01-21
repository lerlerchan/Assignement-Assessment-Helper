from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Student:
    """Represents a student with their assignment content."""

    id: str
    name: str
    content: str
    source_file: str
    page_range: Optional[tuple] = None

    def __post_init__(self):
        # Clean up ID and name
        self.id = self.id.strip() if self.id else "Unknown"
        self.name = self.name.strip() if self.name else "Unknown"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'source_file': self.source_file,
            'page_range': self.page_range
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Student':
        return cls(
            id=data.get('id', 'Unknown'),
            name=data.get('name', 'Unknown'),
            content=data.get('content', ''),
            source_file=data.get('source_file', ''),
            page_range=data.get('page_range')
        )
