# pdf_utils.py

import pdfplumber
import pytesseract
from PIL import Image

def extract_text_and_tables(pdf_path):
    all_text = ""
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()

            # If no text found, apply OCR
            if not text:
                image = page.to_image(resolution=300).original
                text = pytesseract.image_to_string(image)

            all_text += f"\n\n--- Page {page_num} ---\n{text}"

            # Try to extract tables (only works if text-based)
            tables = page.extract_tables()
            for table in tables:
                all_tables.append(table)

    return all_text.strip(), all_tables
