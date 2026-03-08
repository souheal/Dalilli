"""
OCR Service

Handles optical character recognition for scanned documents and images.
Uses Tesseract OCR via pytesseract.

Windows Setup Instructions:
==========================
1. Download Tesseract installer from:
   https://github.com/UB-Mannheim/tesseract/wiki

2. Run the installer (tesseract-ocr-w64-setup-*.exe)
   - Default install path: C:\Program Files\Tesseract-OCR

3. Configure the path in one of two ways:

   Option A: Set environment variable
   - Add to system PATH: C:\Program Files\Tesseract-OCR

   Option B: Set in .env file
   - Add line: TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

4. Install Python packages:
   pip install pytesseract Pillow pdf2image

5. For PDF OCR, also install Poppler:
   - Download from: https://github.com/oschwartz10612/poppler-windows/releases
   - Extract to: C:\Program Files\poppler
   - Add to PATH: C:\Program Files\poppler\Library\bin
"""

import os
import shutil
from typing import Optional, List
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Check for required packages
_PACKAGES_AVAILABLE = True
_IMPORT_ERROR = None

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
except ImportError as e:
    _PACKAGES_AVAILABLE = False
    _IMPORT_ERROR = str(e)


class TesseractNotFoundError(Exception):
    """Raised when Tesseract executable is not found."""
    pass


class OCRPackageError(Exception):
    """Raised when required OCR packages are not installed."""
    pass


class OCRService:
    """
    Service for OCR processing using Tesseract.

    Automatically detects Tesseract installation on Windows.
    Provides clear error messages when dependencies are missing.
    """

    # Common Tesseract installation paths on Windows
    WINDOWS_TESSERACT_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
    ]

    def __init__(self):
        """
        Initialize OCR service.

        Raises:
            OCRPackageError: If pytesseract/Pillow/pdf2image not installed
            TesseractNotFoundError: If Tesseract executable not found
        """
        if not _PACKAGES_AVAILABLE:
            raise OCRPackageError(
                f"OCR packages not installed: {_IMPORT_ERROR}\n\n"
                "Install with:\n"
                "  pip install pytesseract Pillow pdf2image\n\n"
                "Then install Tesseract from:\n"
                "  https://github.com/UB-Mannheim/tesseract/wiki"
            )

        self._configure_tesseract()
        self._verify_tesseract()

    def _configure_tesseract(self):
        """
        Configure Tesseract path.

        Priority:
        1. Settings from config/env
        2. Auto-detect from common Windows paths
        3. System PATH (shutil.which)
        """
        # Check if already configured via settings
        if settings.tesseract_path and os.path.exists(settings.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
            logger.info(f"Using Tesseract from settings: {settings.tesseract_path}")
            return

        # Try common Windows installation paths
        for path in self.WINDOWS_TESSERACT_PATHS:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"Found Tesseract at: {path}")
                return

        # Check if in system PATH
        tesseract_in_path = shutil.which("tesseract")
        if tesseract_in_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_in_path
            logger.info(f"Found Tesseract in PATH: {tesseract_in_path}")
            return

        # Not found - will be caught by _verify_tesseract

    def _verify_tesseract(self):
        """
        Verify Tesseract is working.

        Raises:
            TesseractNotFoundError: If Tesseract not found or not working
        """
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            raise TesseractNotFoundError(
                "Tesseract OCR not found or not working.\n\n"
                "Windows Installation:\n"
                "1. Download from: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. Run the installer\n"
                "3. Either:\n"
                "   - Add to PATH: C:\\Program Files\\Tesseract-OCR\n"
                "   - Or set in .env: TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe\n"
                "4. Restart your terminal/IDE\n\n"
                f"Error: {str(e)}"
            )

    def ocr_image(self, image_path: str, language: str = "eng") -> str:
        """
        Extract text from an image file using OCR.

        Args:
            image_path: Path to the image file (PNG, JPG, etc.)
            language: Tesseract language code (default: 'eng')
                      Use 'eng+fra' for multiple languages

        Returns:
            Extracted text string
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        image = Image.open(image_path)

        # Convert to RGB if necessary (handles RGBA, P mode, etc.)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

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
        Extract text from a specific PDF page using OCR.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number (0-indexed)
            language: Tesseract language code
            dpi: Image resolution for PDF conversion (higher = better OCR but slower)

        Returns:
            Extracted text from the specified page
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Convert specific page to image
        # first_page and last_page are 1-indexed in pdf2image
        try:
            images = convert_from_path(
                pdf_path,
                first_page=page_number + 1,
                last_page=page_number + 1,
                dpi=dpi
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "poppler" in error_msg or "pdftoppm" in error_msg:
                raise RuntimeError(
                    "Poppler not found. Required for PDF OCR.\n\n"
                    "Windows Installation:\n"
                    "1. Download from: https://github.com/oschwartz10612/poppler-windows/releases\n"
                    "2. Extract to: C:\\Program Files\\poppler\n"
                    "3. Add to PATH: C:\\Program Files\\poppler\\Library\\bin\n"
                    "4. Restart your terminal/IDE"
                ) from e
            raise

        if not images:
            return ""

        # OCR the page image
        text = pytesseract.image_to_string(images[0], lang=language)
        return text

    def ocr_pdf_all_pages(
        self,
        pdf_path: str,
        language: str = "eng",
        dpi: int = 300
    ) -> List[str]:
        """
        Extract text from ALL pages of a PDF using OCR.

        Args:
            pdf_path: Path to the PDF file
            language: Tesseract language code
            dpi: Image resolution for conversion

        Returns:
            List of text strings, one per page
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            images = convert_from_path(pdf_path, dpi=dpi)
        except Exception as e:
            error_msg = str(e).lower()
            if "poppler" in error_msg or "pdftoppm" in error_msg:
                raise RuntimeError(
                    "Poppler not found. Required for PDF OCR.\n\n"
                    "Windows Installation:\n"
                    "1. Download from: https://github.com/oschwartz10612/poppler-windows/releases\n"
                    "2. Extract to: C:\\Program Files\\poppler\n"
                    "3. Add to PATH: C:\\Program Files\\poppler\\Library\\bin\n"
                    "4. Restart your terminal/IDE"
                ) from e
            raise

        page_texts = []
        for image in images:
            text = pytesseract.image_to_string(image, lang=language)
            page_texts.append(text)

        return page_texts

    @staticmethod
    def is_available() -> bool:
        """
        Check if OCR functionality is available.

        Returns True only if all dependencies are installed and configured.
        """
        if not _PACKAGES_AVAILABLE:
            return False

        try:
            # Try to get version - this verifies Tesseract is working
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
