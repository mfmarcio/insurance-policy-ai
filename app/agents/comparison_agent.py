from __future__ import annotations

from difflib import SequenceMatcher

from app.models.policy import ComparisonItem, PolicyComparison, PolicyData
from app.services.llm_service import LLMService, LLMServiceError


class ComparisonAgent:
    def __init__(self) -> None:
        self.llm = LLMService()

    def run(self, a: PolicyData, b: PolicyData) -> PolicyComparison:
        items: list[ComparisonItem] = []
        items.extend(self._compare_coverages(a, b))
        items.extend(self._compare_exclusions(a, b))
        items.extend(self._compare_metadata(a, b))
        comparison = PolicyComparison(policy_a_id=a.policy_id, policy_b_id=b.policy_id, items=items)
        comparison.summary = self._summarize(a, b, items)
        return comparison

    def _compare_metadata(self, a: PolicyData, b: PolicyData) -> list[ComparisonItem]:
        rows = []
        for label, va, vb in [
            ("Seguradora", a.insurer, b.insurer),
            ("Produto", a.product, b.product),
            ("Início de vigência", a.effective_start, b.effective_start),
            ("Fim de vigência", a.effective_end, b.effective_end),
        ]:
            rows.append(
                ComparisonItem(
                    dimension="Dados gerais",
                    item=label,
                    policy_a=va,
                    policy_b=vb,
                    status="EQUIVALENTE" if (va or "") == (vb or "") else "DIFERENTE",
                )
            )
        return rows

    def _compare_coverages(self, a: PolicyData, b: PolicyData) -> list[ComparisonItem]:
        result: list[ComparisonItem] = []
        b_used: set[int] = set()
        for ca in a.coverages:
            idx = self._best_match(ca.name, [x.name for x in b.coverages], b_used)
            if idx is None:
                result.append(
                    ComparisonItem(
                        dimension="Cobertura",
                        item=ca.name,
                        policy_a=self._coverage_value(ca),
                        policy_b=None,
                        status="SOMENTE_A",
                        evidence_a=ca.evidence,
                    )
                )
                continue
            b_used.add(idx)
            cb = b.coverages[idx]
            status = self._coverage_status(ca.limit_value, cb.limit_value, ca.deductible_value, cb.deductible_value)
            result.append(
                ComparisonItem(
                    dimension="Cobertura",
                    item=ca.name,
                    policy_a=self._coverage_value(ca),
                    policy_b=self._coverage_value(cb),
                    status=status,
                    evidence_a=ca.evidence,
                    evidence_b=cb.evidence,
                )
            )
        for idx, cb in enumerate(b.coverages):
            if idx not in b_used:
                result.append(
                    ComparisonItem(
                        dimension="Cobertura",
                        item=cb.name,
                        policy_a=None,
                        policy_b=self._coverage_value(cb),
                        status="SOMENTE_B",
                        evidence_b=cb.evidence,
                    )
                )
        return result

    def _compare_exclusions(self, a: PolicyData, b: PolicyData) -> list[ComparisonItem]:
        result: list[ComparisonItem] = []
        b_used: set[int] = set()
        for ea in a.exclusions:
            idx = self._best_match(ea.category, [x.category for x in b.exclusions], b_used)
            if idx is None:
                result.append(ComparisonItem(dimension="Exclusão", item=ea.category, policy_a=ea.description, status="SOMENTE_A", evidence_a=ea.evidence))
                continue
            b_used.add(idx)
            eb = b.exclusions[idx]
            similarity = SequenceMatcher(None, ea.description.lower(), eb.description.lower()).ratio()
            result.append(
                ComparisonItem(
                    dimension="Exclusão",
                    item=ea.category,
                    policy_a=ea.description,
                    policy_b=eb.description,
                    status="EQUIVALENTE" if similarity >= 0.78 else "DIFERENTE",
                    evidence_a=ea.evidence,
                    evidence_b=eb.evidence,
                )
            )
        for idx, eb in enumerate(b.exclusions):
            if idx not in b_used:
                result.append(ComparisonItem(dimension="Exclusão", item=eb.category, policy_b=eb.description, status="SOMENTE_B", evidence_b=eb.evidence))
        return result

    def _summarize(self, a: PolicyData, b: PolicyData, items: list[ComparisonItem]) -> str:
        compact = "\n".join(f"- {i.dimension}/{i.item}: {i.status}; A={i.policy_a}; B={i.policy_b}" for i in items[:40])
        prompt = f"""
Produza um resumo executivo curto, em português, da comparação entre duas apólices.
Não dê aconselhamento jurídico. Destaque diferenças objetivas, pontos favoráveis e itens inconclusivos.

Apólice A: {a.document_name}
Apólice B: {b.document_name}

Resultados estruturados:
{compact}
"""
        try:
            return self.llm.generate_text(prompt)
        except LLMServiceError:
            diffs = sum(1 for i in items if i.status != "EQUIVALENTE")
            return f"Foram comparados {len(items)} critérios; {diffs} apresentam diferença, exclusividade ou inconclusão."

    @staticmethod
    def _best_match(name: str, candidates: list[str], used: set[int]) -> int | None:
        best_idx = None
        best_score = 0.0
        for idx, candidate in enumerate(candidates):
            if idx in used:
                continue
            score = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
            if score > best_score:
                best_idx, best_score = idx, score
        return best_idx if best_score >= 0.55 else None

    @staticmethod
    def _coverage_value(c) -> str:
        parts = []
        if c.limit_value is not None:
            parts.append(f"Limite {c.currency or ''} {c.limit_value:,.2f}".strip())
        if c.deductible_value is not None:
            parts.append(f"Franquia {c.currency or ''} {c.deductible_value:,.2f}".strip())
        elif c.deductible_text:
            parts.append(f"Franquia {c.deductible_text}")
        if c.description:
            parts.append(c.description)
        return " | ".join(parts) if parts else c.name

    @staticmethod
    def _coverage_status(limit_a, limit_b, deductible_a, deductible_b) -> str:
        if limit_a is not None and limit_b is not None and limit_a != limit_b:
            return "MAIS_FAVORAVEL_A" if limit_a > limit_b else "MAIS_FAVORAVEL_B"
        if deductible_a is not None and deductible_b is not None and deductible_a != deductible_b:
            return "MAIS_FAVORAVEL_A" if deductible_a < deductible_b else "MAIS_FAVORAVEL_B"
        if limit_a == limit_b and deductible_a == deductible_b:
            return "EQUIVALENTE"
        return "DIFERENTE"
