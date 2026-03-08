import os
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from app.config import settings


class OCRService:
    """Service for OCR processing of scanned documents"""

    def __init__(self):
        if not OCR_AVAILABLE:
            raise RuntimeError(
                "OCR dependencies not installed. "
                "Install with: pip install pytesseract Pillow pdf2image"
            )

        # Set tesseract path if configured
        if settings.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path

    def ocr_image(self, image_path: str, language: str = "eng") -> str:
        """
        Perform OCR on an image file

        Args:
            image_path: Path to the image file
            language: OCR language (default: English)

        Returns:
            Extracted text
        """
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=language)
        return text

    def ocr_pdf_page(
        self,
        pdf_path: str,
        page_number: int,
        language: str = "eng",
        dpi: int = 300
    ) -> str:
        """
        Perform OCR on a specific PDF page

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number (0-indexed)
            language: OCR language
            dpi: Image resolution for conversion

        Returns:
            Extracted text
        """
        # Convert specific page to image
        images = convert_from_path(
            pdf_path,
            first_page=page_number + 1,
            last_page=page_number + 1,
            dpi=dpi
        )

        if not images:
            return ""

        # Perform OCR
        text = pytesseract.image_to_string(images[0], lang=language)
        return text

    def ocr_pdf_all(
        self,
        pdf_path: str,
        language: str = "eng",
        dpi: int = 300
    ) -> str:
        """
        Perform OCR on all pages of a PDF

        Args:
            pdf_path: Path to the PDF file
            language: OCR language
            dpi: Image resolution for conversion

        Returns:
            Extracted text from all pages
        """
        # Convert all pages to images
        images = convert_from_path(pdf_path, dpi=dpi)

        texts = []
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image, lang=language)
            texts.append(f"[Page {i + 1}]\n{page_text}")

        return "\n\n".join(texts)

    @staticmethod
    def is_available() -> bool:
        """Check if OCR is available"""
        return OCR_AVAILABLE
