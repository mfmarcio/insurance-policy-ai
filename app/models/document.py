from pydantic import BaseModel, Field


class PageText(BaseModel):
    page: int
    text: str
    extraction_method: str


class ExtractedDocument(BaseModel):
    document_id: str
    filename: str
    pages: list[PageText] = Field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n\n".join(f"[PAGE {p.page}]\n{p.text}" for p in self.pages)


class TextChunk(BaseModel):
    chunk_id: str
    page: int
    text: str
