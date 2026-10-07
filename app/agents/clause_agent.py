from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.models.document import TextChunk
from app.models.policy import Coverage, Exclusion, SpecialClause
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService


class ClauseExtraction(BaseModel):
    insurer: str | None = None
    policy_number: str | None = None
    insured_name: str | None = None
    product: str | None = None
    effective_start: str | None = None
    effective_end: str | None = None
    coverages: list[Coverage] = Field(default_factory=list)
    exclusions: list[Exclusion] = Field(default_factory=list)
    special_clauses: list[SpecialClause] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)


class ClauseAgent:
    SEARCH_QUERY = (
        "seguradora número apólice segurado vigência produto cobertura capital segurado limite máximo indenização "
        "franquia participação obrigatória exclusão risco excluído carência obrigação cláusula especial sinistro"
    )

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = LLMService()
        self.retriever = RetrievalService()

    def run(self, chunks: list[TextChunk]) -> ClauseExtraction:
        selected = self.retriever.retrieve(chunks, self.SEARCH_QUERY, self.settings.top_k_chunks)
        if not selected:
            selected = chunks[: self.settings.top_k_chunks]
        context = self.retriever.as_context(selected)
        prompt = f"""
Analise exclusivamente os trechos da apólice abaixo e extraia os dados solicitados no schema JSON.

REGRAS:
- Não invente informações ausentes.
- Use null quando o valor não estiver presente.
- Para coberturas, exclusões e cláusulas, inclua evidência textual curta e número da página.
- confidence deve ficar entre 0 e 1 e refletir a clareza da evidência.
- Valores monetários devem ser numéricos, sem símbolos ou separadores de milhar.
- Preserve o significado jurídico. Não conclua que uma cobertura existe apenas por ela ser citada em uma exclusão.
- Em observations, registre ambiguidades ou informações importantes que não caibam nos demais campos.

TRECHOS:
{context}
"""
        return self.llm.generate_json(prompt, ClauseExtraction)
