# Aptino Policy-Aware Multi-Agent RAG Claim Decision Engine

A production-style take-home implementation for policy-grounded health-insurance claim analysis. The supplied Universal Sompo policy is treated as the authoritative source; synthetic public cases are never modified.

## Architecture

```text
Claim JSON
   |
   v
Case Analysis Agent --> structured investigation plan
   |
   v
Policy Evidence Agent
   |-- dense retrieval (SentenceTransformers; SVD fallback)
   |-- sparse retrieval (BM25)
   |-- Reciprocal Rank Fusion
   `-- cross-encoder reranking (BGE; lexical fallback)
   |
   v
Coverage & Exclusion Agent --> waiting periods / exclusions / definitions / limits
   |
   v
Decision Agent --> machine-readable status + payable estimate
   |
   v
Validation Agent --> citation coverage check; unsupported material claims => NEEDS_REVIEW
   |
   v
FastAPI / Streamlit
```

The agents have separate responsibilities and exchange typed Pydantic/dataclass state. The application exposes concise audit traces, not hidden chain-of-thought.

## Key design choices

- **Meaningful policy chunking:** page-aware paragraph/heading chunks preserve page, section and chunk ID.
- **Hybrid RAG:** dense semantic retrieval and lexical BM25 run independently; RRF fuses them.
- **Reranking:** BGE CrossEncoder is used when available; a deterministic lexical reranker keeps the project runnable without model downloads.
- **Safety-first adjudication:** policy-sensitive outcomes are handled by explicit rules backed by retrieved policy evidence. This reduces hallucinated insurance rules. An optional LLM can be added for extraction, but it is not allowed to override the policy safety layer.
- **Abstention:** unresolved hospital-definition or medical-necessity evidence produces `NEEDS_REVIEW` rather than a guessed decision.

## Setup

Python 3.10+ is required.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/ingest_policy.py
```

Optional: set `OPENAI_API_KEY` if extending the extraction layer with an LLM. No secret is required for the included deterministic evaluation.

## Run API

```bash
uvicorn backend.api.main:app --reload --port 8000
```

Health: `GET http://localhost:8000/health`

Analyze: `POST http://localhost:8000/analyze`

Example request:

```json
{"case": {"case_id":"PUB-001", "policy_id":"USGIC-CSC-2017-2018", "policy_start_date":"2025-01-01", "claim_date":"2026-03-14", "sum_insured_inr":500000, "continuous_coverage_months":14, "prior_insurer_continuous_years":0, "patient":{"age":34}, "hospital":{"name":"Sunrise Multispeciality","network_provider":true}, "treatment":{"type":"inpatient","admission_hours":96,"diagnosis":"Acute appendicitis","procedure":"Appendectomy","pre_existing":false,"experimental":false}, "expenses_inr":{"room":30000,"doctor_fees":30000,"medicines_diagnostics":90000,"pre_hospitalization":5000,"post_hospitalization":7000,"ambulance":1200}, "documents":["claim_form","discharge_summary","itemized_bill","doctor_prescription"], "task":"Determine whether the hospitalization is admissible, identify applicable policy limits, and explain any deductions."}}
```

## Run Streamlit

```bash
streamlit run frontend/app.py
```

## Evaluation

```bash
python evaluation/evaluate.py
```

The evaluation covers all 12 supplied public cases plus five candidate-created cases. Expected public outcomes are documented in `evaluation/expected_public.json`. Results are written to `evaluation/results/latest.json`.

### Evaluation methodology

- **Decision accuracy:** exact match against documented expected labels for the supplied synthetic cases.
- **Abstention:** explicit count of `NEEDS_REVIEW` decisions; public cases include PUB-006 and PUB-011 as evidence-gap scenarios.
- **Retrieval quality:** citation hit count is emitted per case; the retriever also exposes dense, BM25, RRF and rerank scores for offline inspection.
- **Citation correctness:** the Validation Agent checks that every material finding/limit has at least one cited retrieved policy chunk. A future extension can add human-reviewed claim-to-clause labels for formal precision/recall measurement.
- **Failure analysis:** see `evaluation/failure_analysis.md`.

## Known limitations / trade-offs

1. The included environment may not have Hugging Face model weights cached. In that case the system uses a deterministic SVD dense representation and lexical reranking. Installing/caching SentenceTransformers upgrades retrieval quality without changing the architecture.
2. Exact payable amounts are an estimate from the supplied expense categories and stated sub-limits; a real claims system would require full bill-line adjudication and insurer-specific configuration.
3. Policy wording can contain ambiguities or OCR/layout artifacts. The engine abstains where supplied evidence is explicitly unresolved.
4. The public cases are synthetic and their expected labels are an engineering test oracle, not real-world claims advice.

## Failure analysis

See `evaluation/failure_analysis.md` for three representative failure modes and corrective actions.
