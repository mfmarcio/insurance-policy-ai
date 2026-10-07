from pathlib import Path

from app.models.document import ExtractedDocument, PageText
from app.services.ocr_service import OCRService
from app.services.pdf_service import PDFService


class ExtractionAgent:
    def __init__(self) -> None:
        self.pdf = PDFService()
        self.ocr = OCRService()

    def run(self, path: Path, document_id: str) -> ExtractedDocument:
        if path.suffix.lower() == ".pdf":
            extracted = self.pdf.extract_pdf(path, document_id)
            for page in extracted.pages:
                if len(page.text.strip()) < 80:
                    image = self.pdf.render_page(path, page.page)
                    ocr_text = self.ocr.extract_image(image)
                    if len(ocr_text) > len(page.text):
                        page.text = ocr_text
                        page.extraction_method = "tesseract"
            return extracted

        text = self.ocr.extract_file(path)
        return ExtractedDocument(
            document_id=document_id,
            filename=path.name,
            pages=[PageText(page=1, text=text, extraction_method="tesseract")],
        )
