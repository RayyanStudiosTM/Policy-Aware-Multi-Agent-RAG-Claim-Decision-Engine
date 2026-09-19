# Architecture & Design Note

## Policy-Aware Multi-Agent RAG Claim Decision Engine

### 1. Objective

The system analyzes a structured health-insurance claim against an authoritative policy PDF and returns a machine-readable decision supported by inspectable policy evidence.

The design emphasizes:

- Policy grounding
- Hybrid retrieval
- Specialized agents
- Structured state exchange
- Citation traceability
- Validation
- Abstention when evidence is insufficient

---

## 2. High-Level Architecture

```text
Browser
   │
   ▼
Streamlit Frontend
   │
   │ POST /analyze
   ▼
FastAPI
   │
   ▼
LangGraph Workflow
   │
   ├── Case Analysis Agent
   │
   ├── Policy Evidence Agent
   │       │
   │       ▼
   │   Hybrid RAG
   │   ├── Dense Retrieval
   │   ├── BM25
   │   ├── RRF
   │   └── Reranking
   │
   ├── Coverage & Exclusion Agent
   │
   ├── Decision Agent
   │
   └── Validation Agent
   │
   ▼
Structured AnalysisResponse
```

The implementation uses an in-memory dense vector matrix and NumPy similarity for the supplied policy scale. It does not require FAISS.

---

## 3. Agent Boundaries

### Case Analysis Agent

Transforms the raw claim into normalized structured facts.

Responsibilities:

- Extract dates
- Extract patient and hospitalization facts
- Normalize treatment information
- Normalize expenses
- Identify documents
- Identify potentially relevant claim attributes

Output:

```text
case_facts
```

### Policy Evidence Agent

Responsible for policy retrieval and evidence construction.

Responsibilities:

- Build retrieval queries from claim facts
- Run dense retrieval
- Run BM25 retrieval
- Fuse rankings using reciprocal rank fusion
- Rerank candidates
- Preserve page/section/chunk metadata

Output:

```text
policy_evidence[]
```

### Coverage & Exclusion Agent

Interprets retrieved policy evidence for:

- Coverage
- Exclusions
- Waiting periods
- Limits
- Deductions
- Conditions

Output:

```text
coverage_findings[]
```

### Decision Agent

Synthesizes structured facts and evidence into:

```text
decision
confidence
key_findings
applicable_limits
missing_evidence
```

The agent is instructed to ground material conclusions in retrieved policy evidence.

### Validation Agent

Performs post-decision checks.

Examples:

- Required fields present
- Decision is one of the supported statuses
- Material findings have evidence
- Numerical deductions are internally consistent
- Evidence is not obviously contradictory
- Insufficient evidence can result in `NEEDS_REVIEW`

---

## 4. State Flow

The workflow passes structured state:

```text
ClaimCase
    ↓
case_facts
    ↓
policy_evidence[]
    ↓
coverage_findings[]
    ↓
decision
    ↓
validation
    ↓
AnalysisResponse
```

This avoids relying on hidden conversational memory between agents.

The frontend receives an operational execution trace. The trace exposes agent names, status, timing, and structured outputs rather than private chain-of-thought.

---

## 5. Retrieval Design

The policy PDF is converted into meaningful chunks containing:

```text
chunk_id
page
section
text
```

The retrieval sequence is:

```text
Query
  │
  ├──────────────► Dense semantic retrieval
  │
  └──────────────► BM25 lexical retrieval
                         │
                         ▼
                  Reciprocal Rank Fusion
                         │
                         ▼
                    Candidate set
                         │
                         ▼
                 Reranking layer
                         │
                         ▼
                    Top evidence
```

### Dense retrieval

Sentence Transformers are used for semantic retrieval.

Local/default model:

```text
BAAI/bge-small-en-v1.5
```

Memory-constrained deployment:

```text
sentence-transformers/all-MiniLM-L6-v2
```

### Sparse retrieval

BM25 provides exact lexical matching. This is useful for:

- Policy terminology
- Numerical limits
- Waiting periods
- Exclusion wording
- Named procedures

### Reranking

The preferred cross-encoder is:

```text
BAAI/bge-reranker-base
```

For constrained deployments:

```text
USE_CROSS_ENCODER=false
```

causes the system to use a lightweight lexical reranking fallback.

This trade-off prevents the reranker from becoming a single point of failure during deployment.

---

## 6. Evidence and Citation Model

Each retrieved evidence item carries source metadata:

```text
source
page
section
chunk_id
excerpt
dense_score
bm25_score
rrf_score
rerank_score
reranker
```

This allows the final response to show which policy fragment supports a decision.

The system does not treat a model-generated explanation as authoritative by itself. The policy document remains the source of policy evidence.

---

## 7. Decision and Abstention

The engine supports:

```text
ADMISSIBLE
ADMISSIBLE_WITH_LIMITS
PARTIALLY_ADMISSIBLE
NOT_ADMISSIBLE
NEEDS_REVIEW
```

`NEEDS_REVIEW` is important because not every claim contains enough information for a deterministic policy conclusion.

Final evaluation produced:

```text
PUB-006
PUB-011
CUSTOM-006
```

as `NEEDS_REVIEW`.

---

## 8. Final Evaluation

The final completed run evaluated 22 cases:

```text
Public:  12/12 successful
Custom:  10/10 successful
Overall: 22/22 successful
```

Validation:

```text
22/22 PASS
```

Abstention:

```text
3 NEEDS_REVIEW
```

Average duration:

```text
Public:  ~72.47 s/case
Custom:  ~71.12 s/case
```

The 10 additional cases intentionally cover policy boundaries and failure-oriented scenarios.

---

## 9. Engineering Trade-offs

### Accuracy vs memory

Larger embedding and reranking models can increase retrieval quality but consume more memory. Environment variables allow the deployment configuration to choose a smaller embedding model and disable the heavyweight cross-encoder when necessary.

### Explainability vs latency

The system retains citations, evidence metadata, validation, and agent traces. This improves auditability but contributes to end-to-end latency.

### Simplicity vs scale

The supplied policy is only 34 processed chunks, so an in-memory index is simple and reproducible. A larger production system would benefit from a persistent vector/search service with metadata filtering and policy-version management.

### Automation vs human review

The system can make structured recommendations for synthetic cases, but `NEEDS_REVIEW` provides a controlled path when evidence is insufficient. Real claims should retain human adjudication and appropriate governance.

---

## 10. Failure Analysis

### Evaluation timeout

A prior evaluator run did not complete all cases under the shorter/default request timeout.

**Improvement:** run the evaluator with `--timeout 300`.

### Render startup memory

The first Render deployment exceeded 512 MiB during model startup.

**Improvement:** use `all-MiniLM-L6-v2`, disable cross-encoder by default, limit thread parallelism, or allocate more memory.

### Reranker download/network failure

The cross-encoder download previously encountered DNS/network resolution failure.

**Improvement:** retain the lexical reranking fallback and cache/bake models for production environments.

---

## 11. Reproducibility

```bash
pip install -r requirements.txt
python scripts/ingest_policy.py
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
python scripts/evaluate.py --timeout 300
```

Frontend:

```bash
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501
```

---

## 12. Current Limitations

- Synthetic evaluation data
- Single supplied policy document
- In-memory retrieval index
- Relatively high per-case latency
- Memory-sensitive model stack
- No production authentication/rate limiting yet
- No general policy-version registry

These are engineering scope limitations rather than claims about the correctness of the underlying insurance policy.
