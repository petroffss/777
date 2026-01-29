from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path



@dataclass
class PdfTextResult:
    text: str
    pages: int
    ocr_used: bool
    ocr_available: bool


class PdfProcessor:
    def __init__(self, max_pages: int = 5, ocr_mode: str = "auto") -> None:
        self.max_pages = max_pages
        self.ocr_mode = ocr_mode

    def extract_text(self, path: Path) -> PdfTextResult:
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError("pdfplumber is not installed") from exc

        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_read = min(total_pages, self.max_pages)
            texts = []
            for page_index in range(pages_to_read):
                page = pdf.pages[page_index]
                texts.append(page.extract_text() or "")

        combined_text = "\n".join(texts).strip()
        ocr_available = self._ocr_available()
        ocr_used = False

        if self._should_use_ocr(combined_text) and self.ocr_mode != "off":
            if ocr_available and self.ocr_mode in {"auto", "on"}:
                ocr_text = self._extract_text_with_ocr(path, pages_to_read)
                if ocr_text:
                    combined_text = ocr_text
                    ocr_used = True
            else:
                ocr_used = False

        return PdfTextResult(
            text=combined_text,
            pages=total_pages,
            ocr_used=ocr_used,
            ocr_available=ocr_available,
        )

    def _should_use_ocr(self, text: str) -> bool:
        if self.ocr_mode == "on":
            return True
        if not text:
            return True
        alpha_count = sum(char.isalpha() for char in text)
        total_count = len(text)
        if total_count == 0:
            return True
        alpha_ratio = alpha_count / total_count
        return alpha_ratio < 0.3

    def _ocr_available(self) -> bool:
        try:
            import pytesseract  # noqa: F401
            from pdf2image import convert_from_path  # noqa: F401

            return True
        except ImportError:
            return False

    def _extract_text_with_ocr(self, path: Path, pages_to_read: int) -> str:
        try:
            from pdf2image import convert_from_path
            import pytesseract
        except ImportError:
            return ""

        try:
            images = convert_from_path(path, first_page=1, last_page=pages_to_read)
            ocr_texts = []
            for image in images:
                ocr_texts.append(pytesseract.image_to_string(image))
            return "\n".join(ocr_texts).strip()
        except Exception:
            return ""
