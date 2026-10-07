from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    page: int | None = None
    text: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Coverage(BaseModel):
    name: str
    description: str | None = None
    limit_value: float | None = None
    currency: str | None = None
    deductible_value: float | None = None
    deductible_text: str | None = None
    evidence: Evidence | None = None


class Exclusion(BaseModel):
    category: str
    description: str
    evidence: Evidence | None = None


class SpecialClause(BaseModel):
    category: str
    title: str | None = None
    description: str
    evidence: Evidence | None = None


class PolicyData(BaseModel):
    policy_id: str
    document_name: str
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComparisonItem(BaseModel):
    dimension: str
    item: str
    policy_a: str | None = None
    policy_b: str | None = None
    status: Literal[
        "EQUIVALENTE",
        "MAIS_FAVORAVEL_A",
        "MAIS_FAVORAVEL_B",
        "SOMENTE_A",
        "SOMENTE_B",
        "DIFERENTE",
        "INCONCLUSIVO",
    ] = "INCONCLUSIVO"
    rationale: str | None = None
    evidence_a: Evidence | None = None
    evidence_b: Evidence | None = None


class PolicyComparison(BaseModel):
    policy_a_id: str
    policy_b_id: str
    summary: str = ""
    items: list[ComparisonItem] = Field(default_factory=list)
