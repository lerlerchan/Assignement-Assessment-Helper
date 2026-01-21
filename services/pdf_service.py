import os
import io
import re
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from models import Student


class PDFService:
    """Service for PDF extraction and splitting."""

    def __init__(self):
        self.ocr_enabled = OCR_AVAILABLE

    def extract_text(self, pdf_path: str, use_ocr: bool = True) -> str:
        """Extract text from a PDF file."""
        all_text = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()

                # If no text found and OCR is enabled, try OCR
                if not text and use_ocr and self.ocr_enabled:
                    try:
                        image = page.to_image(resolution=300).original
                        text = pytesseract.image_to_string(image)
                    except Exception:
                        text = ""

                if text:
                    all_text.append(f"--- Page {page_num} ---\n{text}")

        return "\n\n".join(all_text)

    def extract_text_and_tables(self, pdf_path: str) -> Tuple[str, List[List]]:
        """Extract text and tables from a PDF file."""
        all_text = []
        all_tables = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()

                # If no text found and OCR is enabled, try OCR
                if not text and self.ocr_enabled:
                    try:
                        image = page.to_image(resolution=300).original
                        text = pytesseract.image_to_string(image)
                    except Exception:
                        text = ""

                if text:
                    all_text.append(f"--- Page {page_num} ---\n{text}")

                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        all_tables.append(table)

        return "\n\n".join(all_text), all_tables

    def get_page_count(self, pdf_path: str) -> int:
        """Get the number of pages in a PDF."""
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)

    def split_pdf_by_pages(self, pdf_path: str, pages_per_split: int,
                           output_dir: str) -> List[str]:
        """
        Split a PDF into multiple PDFs with specified pages per split.
        Returns list of output file paths.
        """
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        output_files = []

        base_name = Path(pdf_path).stem
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for start_page in range(0, total_pages, pages_per_split):
            end_page = min(start_page + pages_per_split, total_pages)
            writer = PdfWriter()

            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])

            output_filename = f"{base_name}_pages_{start_page + 1}-{end_page}.pdf"
            output_path = os.path.join(output_dir, output_filename)

            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            output_files.append(output_path)

        return output_files

    def split_pdf_by_marker(self, pdf_path: str, marker_pattern: str,
                            output_dir: str) -> List[Tuple[str, str]]:
        """
        Split a PDF by finding a text marker pattern (e.g., student ID).
        Returns list of (output_path, marker_value) tuples.
        """
        reader = PdfReader(pdf_path)
        base_name = Path(pdf_path).stem
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        results = []
        current_writer = None
        current_marker = None
        start_page = 0

        pattern = re.compile(marker_pattern, re.IGNORECASE)

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                match = pattern.search(text)

                if match:
                    # Save previous section if exists
                    if current_writer and current_marker:
                        output_filename = f"{base_name}_{current_marker}.pdf"
                        output_path = os.path.join(output_dir, output_filename)
                        with open(output_path, 'wb') as f:
                            current_writer.write(f)
                        results.append((output_path, current_marker))

                    # Start new section
                    current_writer = PdfWriter()
                    current_marker = match.group(1) if match.groups() else match.group()
                    current_marker = re.sub(r'[^\w\-]', '_', current_marker)  # Sanitize filename

                if current_writer:
                    current_writer.add_page(reader.pages[page_num])

            # Save last section
            if current_writer and current_marker:
                output_filename = f"{base_name}_{current_marker}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                with open(output_path, 'wb') as f:
                    current_writer.write(f)
                results.append((output_path, current_marker))

        return results

    def extract_students_from_combined(self, pdf_path: str,
                                       pages_per_student: int = None,
                                       student_id_pattern: str = None) -> List[Student]:
        """
        Extract individual student assignments from a combined PDF.

        Args:
            pdf_path: Path to the combined PDF
            pages_per_student: If known, split by page count
            student_id_pattern: Regex pattern to find student ID markers
        """
        students = []

        if pages_per_student:
            # Split by fixed page count
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

                for start in range(0, total_pages, pages_per_student):
                    end = min(start + pages_per_student, total_pages)
                    content_parts = []

                    for page_num in range(start, end):
                        text = pdf.pages[page_num].extract_text()
                        if not text and self.ocr_enabled:
                            try:
                                image = pdf.pages[page_num].to_image(resolution=300).original
                                text = pytesseract.image_to_string(image)
                            except:
                                text = ""
                        content_parts.append(text or "")

                    content = "\n\n".join(content_parts)
                    student_info = self._extract_student_info(content)

                    students.append(Student(
                        id=student_info.get('id', f'Student_{len(students) + 1}'),
                        name=student_info.get('name', 'Unknown'),
                        content=content,
                        source_file=pdf_path,
                        page_range=(start + 1, end)
                    ))

        elif student_id_pattern:
            # Split by student ID pattern
            pattern = re.compile(student_id_pattern, re.IGNORECASE)

            with pdfplumber.open(pdf_path) as pdf:
                current_content = []
                current_info = {}
                current_start = 1

                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    match = pattern.search(text)

                    if match and current_content:
                        # Save previous student
                        content = "\n\n".join(current_content)
                        students.append(Student(
                            id=current_info.get('id', f'Student_{len(students) + 1}'),
                            name=current_info.get('name', 'Unknown'),
                            content=content,
                            source_file=pdf_path,
                            page_range=(current_start, page_num - 1)
                        ))
                        current_content = []
                        current_start = page_num

                    if match:
                        current_info = {
                            'id': match.group(1) if match.groups() else match.group()
                        }

                    if not text and self.ocr_enabled:
                        try:
                            image = page.to_image(resolution=300).original
                            text = pytesseract.image_to_string(image)
                        except:
                            text = ""

                    current_content.append(text)

                # Save last student
                if current_content:
                    content = "\n\n".join(current_content)
                    info = self._extract_student_info(content) if not current_info else current_info
                    students.append(Student(
                        id=info.get('id', f'Student_{len(students) + 1}'),
                        name=info.get('name', 'Unknown'),
                        content=content,
                        source_file=pdf_path,
                        page_range=(current_start, len(pdf.pages))
                    ))
        else:
            # Treat entire PDF as one student
            content = self.extract_text(pdf_path)
            student_info = self._extract_student_info(content)

            students.append(Student(
                id=student_info.get('id', 'Student_1'),
                name=student_info.get('name', 'Unknown'),
                content=content,
                source_file=pdf_path
            ))

        return students

    def _extract_student_info(self, content: str) -> Dict[str, str]:
        """Extract student ID and name from content using common patterns."""
        info = {'id': 'Unknown', 'name': 'Unknown'}

        # Common student ID patterns
        id_patterns = [
            r'Student\s*ID[:\s]+([A-Za-z0-9\-]+)',
            r'ID[:\s]+([A-Za-z0-9\-]+)',
            r'Roll\s*No[.:\s]+([A-Za-z0-9\-]+)',
            r'Registration[:\s]+([A-Za-z0-9\-]+)',
            r'Matric(?:ulation)?\s*(?:No)?[.:\s]+([A-Za-z0-9\-]+)',
        ]

        # Common name patterns
        name_patterns = [
            r'Name[:\s]+([A-Za-z\s\.]+?)(?:\n|Student|ID|$)',
            r'Student\s*Name[:\s]+([A-Za-z\s\.]+?)(?:\n|ID|$)',
            r'By[:\s]+([A-Za-z\s\.]+?)(?:\n|$)',
            r'Submitted\s+by[:\s]+([A-Za-z\s\.]+?)(?:\n|$)',
        ]

        # Try to find ID
        for pattern in id_patterns:
            match = re.search(pattern, content[:1500], re.IGNORECASE)
            if match:
                info['id'] = match.group(1).strip()
                break

        # Try to find name
        for pattern in name_patterns:
            match = re.search(pattern, content[:1500], re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up name (remove extra spaces, limit length)
                name = ' '.join(name.split())[:50]
                if name and len(name) > 1:
                    info['name'] = name
                    break

        return info

    def extract_from_individual_pdfs(self, pdf_paths: List[str]) -> List[Student]:
        """Extract students from multiple individual PDF files."""
        students = []

        for pdf_path in pdf_paths:
            content = self.extract_text(pdf_path)
            student_info = self._extract_student_info(content)

            # Use filename as fallback for ID
            filename = Path(pdf_path).stem
            if student_info['id'] == 'Unknown':
                # Try to extract ID from filename
                id_match = re.search(r'([A-Za-z0-9\-_]+)', filename)
                if id_match:
                    student_info['id'] = id_match.group(1)

            students.append(Student(
                id=student_info.get('id', filename),
                name=student_info.get('name', 'Unknown'),
                content=content,
                source_file=pdf_path
            ))

        return students
