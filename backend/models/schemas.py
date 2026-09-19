from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict

DecisionStatus = Literal["ADMISSIBLE", "ADMISSIBLE_WITH_LIMITS", "PARTIALLY_ADMISSIBLE", "NOT_ADMISSIBLE", "NEEDS_REVIEW"]

class ClaimCase(BaseModel):
    model_config = ConfigDict(extra="allow")
    case_id: str
    policy_id: str
    policy_start_date: str
    claim_date: str
    sum_insured_inr: float
    continuous_coverage_months: int = 0
    prior_insurer_continuous_years: int = 0
    patient: dict[str, Any]
    hospital: dict[str, Any]
    treatment: dict[str, Any]
    expenses_inr: dict[str, float] = Field(default_factory=dict)
    documents: list[str] = Field(default_factory=list)
    task: str = ""
    prior_policy: dict[str, Any] | None = None
    evidence_context: dict[str, Any] | None = None
    expense_timing: dict[str, Any] | None = None

class Citation(BaseModel):
    claim: str
    source: str = "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf"
    page: int
    section: str
    chunk_id: str
    excerpt: str | None = None

class Limit(BaseModel):
    name: str
    allowed_inr: float | None = None
    claimed_inr: float | None = None
    deduction_inr: float = 0
    basis: str
    citation_ids: list[str] = Field(default_factory=list)

class Finding(BaseModel):
    dimension: str
    conclusion: str
    material: bool = True
    citation_ids: list[str] = Field(default_factory=list)

class AgentTrace(BaseModel):
    agent: str
    action: str
    duration_ms: float
    retrieval_count: int = 0
    status: str = "OK"

class Validation(BaseModel):
    status: Literal["PASS", "FAIL", "REVIEW"]
    unsupported_claims: list[str] = Field(default_factory=list)
    revision_signal: str | None = None

class AnalysisResponse(BaseModel):
    case_id: str
    decision: DecisionStatus
    confidence: float = Field(ge=0, le=1)
    key_findings: list[Finding]
    applicable_limits: list[Limit]
    missing_evidence: list[str]
    citations: list[Citation]
    validation: Validation
    trace: list[AgentTrace]
    payable_estimate_inr: float | None = None

class AnalyzeRequest(BaseModel):
    case: ClaimCase
