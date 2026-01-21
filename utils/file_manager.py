import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
import uuid


class FileManager:
    """Manages file operations for the grading assistant."""

    def __init__(self, base_dir: str = 'uploads'):
        self.base_dir = Path(base_dir)
        self.temp_dir = Path(tempfile.gettempdir()) / 'grading_assistant'
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.base_dir / 'assignments').mkdir(exist_ok=True)
        (self.base_dir / 'rubrics').mkdir(exist_ok=True)
        (self.base_dir / 'exports').mkdir(exist_ok=True)
        (self.base_dir / 'sessions').mkdir(exist_ok=True)

    def save_uploaded_file(self, file, category: str = 'assignments') -> Tuple[str, str]:
        """
        Save an uploaded file with a unique name.
        Returns: (saved_path, original_filename)
        """
        original_filename = file.filename
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        ext = Path(original_filename).suffix
        new_filename = f"{timestamp}_{unique_id}{ext}"

        save_path = self.base_dir / category / new_filename
        file.save(str(save_path))

        return str(save_path), original_filename

    def save_temp_file(self, content: bytes, extension: str = '.pdf') -> str:
        """Save content to a temporary file."""
        unique_id = str(uuid.uuid4())[:8]
        filename = f"temp_{unique_id}{extension}"
        filepath = self.temp_dir / filename
        filepath.write_bytes(content)
        return str(filepath)

    def get_session_dir(self, session_id: str) -> Path:
        """Get or create a session directory."""
        session_dir = self.base_dir / 'sessions' / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def list_files(self, category: str = 'assignments', extension: str = '.pdf') -> List[Path]:
        """List files in a category directory."""
        category_dir = self.base_dir / category
        if not category_dir.exists():
            return []
        return sorted(category_dir.glob(f'*{extension}'), key=lambda p: p.stat().st_mtime, reverse=True)

    def delete_file(self, filepath: str) -> bool:
        """Delete a file safely."""
        try:
            path = Path(filepath)
            if path.exists() and path.is_file():
                # Security check: ensure file is within our managed directories
                if self.base_dir in path.parents or self.temp_dir in path.parents:
                    path.unlink()
                    return True
        except Exception as e:
            print(f"Error deleting file: {e}")
        return False

    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up old temporary files."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)

        for filepath in self.temp_dir.glob('*'):
            try:
                if filepath.is_file() and filepath.stat().st_mtime < cutoff:
                    filepath.unlink()
            except Exception:
                pass

    def cleanup_session(self, session_id: str):
        """Clean up a session directory."""
        session_dir = self.base_dir / 'sessions' / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)

    def get_export_path(self, filename: str) -> str:
        """Get a path for an export file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        export_filename = f"{name}_{timestamp}{ext}"
        return str(self.base_dir / 'exports' / export_filename)

    def file_exists(self, filepath: str) -> bool:
        """Check if a file exists."""
        return Path(filepath).exists()

    def get_file_size(self, filepath: str) -> int:
        """Get file size in bytes."""
        path = Path(filepath)
        return path.stat().st_size if path.exists() else 0

    def read_file(self, filepath: str) -> Optional[bytes]:
        """Read file contents."""
        try:
            return Path(filepath).read_bytes()
        except Exception:
            return None
