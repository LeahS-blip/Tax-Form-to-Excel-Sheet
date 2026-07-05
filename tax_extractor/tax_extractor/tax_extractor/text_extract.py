"""
Turn a PDF into (a) a flat text dump for form-type detection, and (b) a list
of positioned words for the positional parser.

Strategy:
  1. Try native extraction with pdfplumber. If a page yields a reasonable
     amount of text, it's a digital PDF -> use it directly. Fast, exact, local.
  2. If pages come back nearly empty, the PDF is almost certainly scanned.
     Fall back to OCR (pytesseract) IF it's installed. OCR is optional so the
     package works out of the box for the common digital-PDF case.
"""

from __future__ import annotations
from dataclasses import dataclass

import pdfplumber


@dataclass
class Word:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    page: int

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def cy(self) -> float:
        return (self.top + self.bottom) / 2


@dataclass
class ExtractedDoc:
    text: str            # full concatenated text, reading order
    words: list[Word]    # all positioned words across pages
    source: str          # "native" or "ocr"
    n_pages: int
    page_texts: list[str] = None  # text per page, for splitting combined PDFs


_MIN_CHARS_PER_PAGE = 40  # below this, assume the page is scanned/empty


def _native(path: str) -> tuple[str, list[Word], int, int]:
    texts: list[str] = []
    words: list[Word] = []
    char_total = 0
    with pdfplumber.open(path) as pdf:
        n_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            char_total += len(page_text.strip())
            texts.append(page_text)
            for w in page.extract_words(use_text_flow=True, keep_blank_chars=False):
                words.append(Word(
                    text=w["text"], x0=w["x0"], x1=w["x1"],
                    top=w["top"], bottom=w["bottom"], page=i,
                ))
    return texts, words, n_pages, char_total


def _ocr(path: str) -> tuple[str, list[Word], int]:
    """OCR fallback. Requires pytesseract, pdf2image, and the poppler + tesseract
    system binaries. Raises a clear error if they're missing."""
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as e:
        raise RuntimeError(
            "This PDF appears to be scanned (no embedded text) and OCR support "
            "is not installed. Install with:  pip install pytesseract pdf2image  "
            "and install the system packages 'tesseract-ocr' and 'poppler-utils'."
        ) from e

    images = convert_from_path(path, dpi=300)
    texts: list[str] = []
    words: list[Word] = []
    for i, img in enumerate(images):
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        line_text: list[str] = []
        # pdfplumber uses PDF points (72/inch); convert OCR pixels at 300 dpi.
        scale = 72.0 / 300.0
        for j, txt in enumerate(data["text"]):
            if not txt.strip():
                continue
            x, y = data["left"][j] * scale, data["top"][j] * scale
            w_, h_ = data["width"][j] * scale, data["height"][j] * scale
            words.append(Word(txt, x, x + w_, y, y + h_, i))
            line_text.append(txt)
        texts.append(" ".join(line_text))
    return texts, words, len(images)


def extract(path: str, force_ocr: bool = False) -> ExtractedDoc:
    if not force_ocr:
        texts, words, n_pages, char_total = _native(path)
        if char_total >= _MIN_CHARS_PER_PAGE * max(1, n_pages) * 0.3:
            return ExtractedDoc("\n".join(texts), words, "native", n_pages, texts)
    # Scanned (or forced): OCR.
    texts, words, n_pages = _ocr(path)
    return ExtractedDoc("\n".join(texts), words, "ocr", n_pages, texts)
