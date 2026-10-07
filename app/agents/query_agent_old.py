from pydantic import BaseModel, Field

from app.models.policy import Evidence, PolicyData
from app.services.llm_service import LLMService


class QueryAnswer(BaseModel):
    answer: str
    evidence: list[Evidence] = Field(default_factory=list)
    inconclusive: bool = False


class QueryAgent:
    """Answers questions using only the already structured policy data and its evidence."""

    def __init__(self) -> None:
        self.llm = LLMService()

    def run(self, policy: PolicyData, question: str) -> QueryAnswer:
        prompt = f"""
Responda à pergunta usando EXCLUSIVAMENTE os dados estruturados da apólice abaixo.

REGRAS:
- Não invente informações.
- Se a informação não estiver disponível, diga que não foi identificada e marque inconclusive=true.
- Sempre que possível, retorne em evidence as evidências já existentes no JSON, preservando página e texto.
- Não dê aconselhamento jurídico.
- Responda de forma objetiva, em português.

PERGUNTA:
{question}

APÓLICE ESTRUTURADA:
{policy.model_dump_json(indent=2)}
"""
        return self.llm.generate_json(prompt, QueryAnswer)
