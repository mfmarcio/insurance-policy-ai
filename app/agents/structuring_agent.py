from app.agents.clause_agent import ClauseExtraction
from app.models.policy import PolicyData


class StructuringAgent:
    def run(self, document_id: str, document_name: str, extraction: ClauseExtraction) -> PolicyData:
        return PolicyData(
            policy_id=document_id,
            document_name=document_name,
            insurer=extraction.insurer,
            policy_number=extraction.policy_number,
            insured_name=extraction.insured_name,
            product=extraction.product,
            effective_start=extraction.effective_start,
            effective_end=extraction.effective_end,
            coverages=extraction.coverages,
            exclusions=extraction.exclusions,
            special_clauses=extraction.special_clauses,
            observations=extraction.observations,
        )
