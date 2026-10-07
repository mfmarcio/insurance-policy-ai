from app.config.settings import get_settings
from app.models.document import ExtractedDocument, TextChunk


class ChunkingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def chunk_document(self, document: ExtractedDocument) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        max_chars = self.settings.max_chars_per_chunk
        overlap = min(self.settings.chunk_overlap, max_chars // 3)
        counter = 0

        for page in document.pages:
            text = page.text.strip()
            if not text:
                continue
            start = 0
            while start < len(text):
                end = min(start + max_chars, len(text))
                segment = text[start:end].strip()
                if segment:
                    counter += 1
                    chunks.append(
                        TextChunk(
                            chunk_id=f"{document.document_id}-p{page.page}-c{counter}",
                            page=page.page,
                            text=segment,
                        )
                    )
                if end >= len(text):
                    break
                start = max(end - overlap, start + 1)
        return chunks
