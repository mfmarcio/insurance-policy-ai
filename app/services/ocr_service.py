from pathlib import Path

from PIL import Image
import pytesseract

from app.config.settings import get_settings


class OCRService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def extract_image(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(image, lang=self.settings.ocr_language).strip()

    def extract_file(self, path: Path) -> str:
        with Image.open(path) as image:
            return self.extract_image(image.convert("RGB"))
