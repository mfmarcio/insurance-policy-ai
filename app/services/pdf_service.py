from pathlib import Path

import fitz
from PIL import Image

from app.models.document import ExtractedDocument, PageText


class PDFService:
    def extract_pdf(self, path: Path, document_id: str) -> ExtractedDocument:
        doc = fitz.open(path)
        pages: list[PageText] = []
        for idx, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            pages.append(PageText(page=idx, text=text, extraction_method="pymupdf"))
        return ExtractedDocument(document_id=document_id, filename=path.name, pages=pages)

    def render_page(self, path: Path, page_number: int, dpi: int = 220) -> Image.Image:
        doc = fitz.open(path)
        page = doc[page_number - 1]
        zoom = dpi / 72
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
