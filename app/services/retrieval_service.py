from collections.abc import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.document import TextChunk


class RetrievalService:
    def retrieve(self, chunks: list[TextChunk], query: str, top_k: int = 8) -> list[TextChunk]:
        if not chunks:
            return []
        corpus = [c.text for c in chunks]
        vectorizer = TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2), max_features=30000)
        matrix = vectorizer.fit_transform(corpus + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
        ranked = scores.argsort()[::-1][:top_k]
        return [chunks[i] for i in ranked if scores[i] > 0]

    @staticmethod
    def as_context(chunks: Iterable[TextChunk]) -> str:
        return "\n\n".join(f"[PÁGINA {c.page}]\n{c.text}" for c in chunks)
