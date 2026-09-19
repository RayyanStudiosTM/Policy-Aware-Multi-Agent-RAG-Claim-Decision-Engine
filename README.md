# Policy-Aware Multi-Agent RAG Claim Decision Engine

**Live Frontend:** https://aptino-claim-frontend.onrender.com  
**Live API:** https://aptino-claim-api.onrender.com  
**API Docs:** https://aptino-claim-api.onrender.com/docs  
**GitHub Repository:** https://github.com/RayyanStudiosTM/Policy-Aware-Multi-Agent-RAG-Claim-Decision-Engine

An AI-powered, policy-grounded health-insurance claim analysis system built for the Aptino AI Engineer take-home assignment.

# Policy-Aware Multi-Agent RAG Claim Decision Engine

An AI-powered, policy-grounded health-insurance claim analysis system built for the Aptino AI Engineer take-home assignment.

**Repository:** https://github.com/RayyanStudiosTM/Policy-Aware-Multi-Agent-RAG-Claim-Decision-Engine

## 1. Project Overview

The system analyzes a synthetic health-insurance claim against an authoritative policy PDF and produces a structured decision with:

- Claim admissibility status
- Applicable policy limits and exclusions
- Numerical deductions where applicable
- Missing or insufficient evidence
- Inspectable policy citations
- Validation status
- Agent execution trace
- Confidence

Supported decision statuses:

`ADMISSIBLE` • `ADMISSIBLE_WITH_LIMITS` • `PARTIALLY_ADMISSIBLE` • `NOT_ADMISSIBLE` • `NEEDS_REVIEW`

The design intentionally separates claim interpretation, policy evidence retrieval, coverage/exclusion analysis, decision synthesis, and validation.

---

## 2. Architecture

```text
                         ┌──────────────────────┐
                         │      Streamlit       │
                         │      Frontend        │
                         └──────────┬───────────┘
                                    │ POST /analyze
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │        API           │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │      LangGraph       │
                         │ Multi-Agent Workflow │
                         └──────────┬───────────┘
                                    │
            ┌───────────────────────┼────────────────────────┐
            ▼                       ▼                        ▼
     Case Analysis Agent     Policy Evidence Agent    Coverage & Exclusion
                                                            Agent
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Hybrid RAG      │
                         │                      │
                         │ Dense Retrieval      │
                         │ BM25 Sparse Search   │
                         │ Reciprocal Rank      │
                         │ Fusion + Reranking   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Indexed Policy PDF   │
                         │ page / section / ID  │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │    Decision Agent    │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │   Validation Agent   │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Structured Response  │
                         │ decision             │
                         │ findings             │
                         │ limits               │
                         │ citations            │
                         │ validation           │
                         │ trace                │
                         └──────────────────────┘
```

### Agent boundaries

1. **Case Analysis Agent**
   - Normalizes the claim.
   - Extracts treatment, hospitalization, expenses, documents, dates, and relevant attributes.
   - Produces structured claim facts.

2. **Policy Evidence Agent**
   - Converts claim facts into policy retrieval queries.
   - Searches the indexed policy using dense and BM25 retrieval.
   - Fuses candidate rankings using reciprocal rank fusion.
   - Applies cross-encoder reranking when enabled; otherwise uses the lightweight lexical reranker.
   - Returns evidence with page, section, chunk ID, and excerpt metadata.

3. **Coverage & Exclusion Agent**
   - Maps retrieved policy clauses to coverage conditions, exclusions, waiting periods, limits, and deductions.
   - Produces structured coverage findings.

4. **Decision Agent**
   - Synthesizes the structured claim facts and policy findings.
   - Produces one of the supported decision statuses.
   - Attaches evidence references to material findings.

5. **Validation Agent**
   - Checks decision consistency.
   - Checks required fields and citation coverage.
   - Detects unsupported or contradictory conclusions.
   - Marks the result for review when the evidence is insufficient.

No hidden chain-of-thought is exposed. The frontend displays an operational trace containing agent names, status, timing, and structured outputs.

---

## 3. State Flow

The agents exchange a structured state rather than free-form conversational messages.

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

The response is machine-readable and includes the evidence required to inspect material policy claims.

---

## 4. Hybrid RAG Design

The policy PDF is processed into meaningful chunks with:

- `chunk_id`
- `page`
- `section`
- `text`

The current retrieval pipeline is:

```text
Query
  ├── Dense semantic retrieval
  └── BM25 sparse retrieval
          ↓
   Reciprocal Rank Fusion
          ↓
 Candidate reranking
          ↓
 Top policy evidence
```

### Dense retrieval

The dense retriever uses Sentence Transformers. The default local model is:

```text
BAAI/bge-small-en-v1.5
```

For memory-constrained deployment, the environment can use:

```text
sentence-transformers/all-MiniLM-L6-v2
```

### Sparse retrieval

BM25 provides lexical matching for policy terms, numbers, exclusions, waiting periods, and other exact language.

### Reranking

The system supports:

```text
BAAI/bge-reranker-base
```

When `USE_CROSS_ENCODER=false`, the system uses the lightweight lexical reranking fallback. This makes deployment more practical on low-memory infrastructure while preserving the hybrid retrieval architecture.

**Important:** the implementation uses an in-memory dense vector matrix and NumPy similarity, not FAISS.

---

## 5. Policy Grounding and Citations

The policy PDF is treated as the authoritative policy source for the engine.

Every evidence item retains:

- Source document
- Page
- Section
- Chunk ID
- Text excerpt
- Retrieval scores

Material decision findings are expected to reference the retrieved evidence. This allows an evaluator to inspect why a policy condition or limit was applied.

---

## 6. Abstention / NEEDS_REVIEW

The engine does not force every case into an admissible or non-admissible outcome.

`NEEDS_REVIEW` is used when the available evidence does not support a sufficiently reliable decision.

The final evaluation produced three `NEEDS_REVIEW` cases:

- `PUB-006`
- `PUB-011`
- `CUSTOM-006`

This satisfies the requirement to demonstrate evidence-aware abstention.

---

## 7. API

### Health

```http
GET /health
```

Example:

```json
{
  "status": "ok",
  "service": "aptino-claim-engine"
}
```

### Analyze

```http
POST /analyze
Content-Type: application/json
```

Request:

```json
{
  "case": {
    "...": "claim case"
  }
}
```

The response contains the structured decision, evidence, findings, validation information, and execution trace.

Interactive API documentation is available through FastAPI at:

```text
/docs
```

when the API is running.

---

## 8. Project Structure

```text
aptino-claim-engine/
├── backend/
│   ├── agents/
│   ├── api/
│   ├── models/
│   ├── rag/
│   ├── retrieval/
│   └── services/
├── data/
│   ├── public_cases/
│   └── claim_case_schema.md
├── evaluation/
│   ├── custom_cases.json
│   ├── expected_public.json
│   ├── expected_sections.json
│   ├── failure_analysis.md
│   ├── metrics.py
│   └── results/
├── frontend/
│   └── app.py
├── policy/
│   ├── source/
│   └── processed/
├── scripts/
│   ├── evaluate.py
│   └── ingest_policy.py
├── tests/
├── requirements.txt
├── render.yaml
└── README.md
```

---

## 9. Local Setup

### Requirements

- Python 3.10+
- Git
- OpenAI API key for LLM-based decision synthesis
- Internet access during first model download

### Install

```bash
git clone https://github.com/RayyanStudiosTM/Policy-Aware-Multi-Agent-RAG-Claim-Decision-Engine.git
cd Policy-Aware-Multi-Agent-RAG-Claim-Decision-Engine

python -m venv .venv
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment

Create `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
RERANK_MODEL=BAAI/bge-reranker-base
USE_CROSS_ENCODER=false
```

Never commit a real API key. `.env` is ignored by Git.

### Policy ingestion

If the processed policy index does not exist:

```bash
python scripts/ingest_policy.py
```

The current processed policy contains 34 chunks.

### Start API

```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### Start frontend

In a second terminal:

```bash
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501
```

Local URLs:

```text
API:      http://localhost:8000
API docs: http://localhost:8000/docs
Frontend: http://localhost:8501
```

---

## 10. Production / Render Configuration

Backend service:

```text
Build:
pip install -r requirements.txt

Start:
uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
```

Recommended backend environment variables for a 512 MB-class deployment:

```text
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RERANK_MODEL=BAAI/bge-reranker-base
USE_CROSS_ENCODER=false
```

The smaller embedding model and disabled heavyweight cross-encoder reduce startup memory pressure.

Frontend service:

```text
Build:
pip install -r requirements.txt

Start:
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port $PORT
```

Frontend environment:

```text
API_URL=https://YOUR-BACKEND.onrender.com
```

The frontend should use `API_URL` rather than assuming the backend is always on localhost.

**Live deployment URLs should be added here after the final Render services are verified.**

---

## 11. Evaluation

The final completed local evaluation was run with:

```bash
python scripts/evaluate.py --timeout 300
```

### Public cases

- Total: **12**
- Successful: **12**
- Failed: **0**
- Validation PASS: **12**
- NEEDS_REVIEW: **2**
- Average duration: **72.47 seconds**

Decision distribution:

| Decision | Cases |
|---|---:|
| ADMISSIBLE_WITH_LIMITS | 3 |
| NOT_ADMISSIBLE | 4 |
| ADMISSIBLE | 3 |
| NEEDS_REVIEW | 2 |

NEEDS_REVIEW:

```text
PUB-006
PUB-011
```

### Custom cases

- Total: **10**
- Successful: **10**
- Failed: **0**
- Validation PASS: **10**
- NEEDS_REVIEW: **1**
- Average duration: **71.12 seconds**

Decision distribution:

| Decision | Cases |
|---|---:|
| ADMISSIBLE_WITH_LIMITS | 4 |
| ADMISSIBLE | 3 |
| NOT_ADMISSIBLE | 2 |
| NEEDS_REVIEW | 1 |

NEEDS_REVIEW:

```text
CUSTOM-006
```

### Overall

| Metric | Result |
|---|---:|
| Total cases | 22 |
| Successful | 22 |
| Failed | 0 |
| NEEDS_REVIEW | 3 |
| Public cases | 12/12 |
| Custom cases | 10/10 |
| Validation PASS | 22/22 |

The evaluation artifacts are saved by the evaluator as:

```text
evaluation/public_results.json
evaluation/custom_results.json
evaluation/evaluation_summary.json
```

See `EVALUATION_RESULTS.md` for the detailed report.

---

## 12. Additional Test Cases

Ten candidate-created custom cases are included:

1. Room + ambulance sub-limits
2. Waiting-period scenario
3. Insufficient-evidence scenario
4. Experimental-treatment exclusion
5. Pre-existing-condition scenario
6. Outpatient coverage boundary
7. Multiple policy sections
8. Irrelevant attributes
9. Uncertain/incomplete condition
10. Multiple limits and numerical deductions

The purpose is to test both ordinary decisions and boundary conditions rather than only straightforward positive cases.

---

## 13. Failure Analysis and Improvements

### 1. Evaluation timeout

An earlier evaluator run using the default timeout did not complete all public cases; one case timed out.

**Improvement:** the evaluation client was rerun with a 300-second request timeout. The final run completed all 22 cases successfully.

### 2. Render memory pressure

The first Render deployment exceeded the available 512 MiB memory during startup. The failure occurred while loading the retrieval/model stack; the port detection messages were a consequence of the process being terminated.

**Improvement:**

- Use `all-MiniLM-L6-v2` for memory-constrained deployment.
- Disable the heavyweight cross-encoder by default in low-memory production.
- Limit CPU/thread parallelism.
- Keep the lexical reranking fallback.
- Upgrade the service memory if a full cross-encoder is required.

### 3. Reranker/model download reliability

Model downloads can fail in restricted or DNS-constrained environments.

**Improvement:** retrieval remains operational through the lexical reranking fallback when the cross-encoder cannot be loaded. For production, models should ideally be cached or baked into the deployment image.

### Performance limitation

The final local evaluation averaged approximately 71–72 seconds per case. The architecture prioritizes evidence traceability and multi-agent processing over minimal latency.

---

## 14. Security

- API keys are stored through environment variables.
- `.env` is ignored by Git.
- `.env.example` contains only placeholders.
- No real claimant personal information is required by the supplied synthetic case format.
- Production deployments should add authentication, rate limiting, HTTPS, request logging controls, and secret management before handling sensitive real-world claims.

---

## 15. Known Limitations

1. The evaluation uses synthetic claims.
2. The policy source is a fixed document; policy-version selection is not yet a general policy registry.
3. Retrieval is in-memory and suitable for the supplied policy scale; a larger production corpus would benefit from a persistent vector/search service.
4. The default production configuration may use lightweight lexical reranking instead of the heavyweight cross-encoder to satisfy memory constraints.
5. End-to-end latency is relatively high for an interactive claim workflow.
6. This is a decision-support engine, not a substitute for a human claims adjudication process.

---

## 16. Design Trade-offs

### Accuracy vs memory

A larger embedding model and cross-encoder can improve retrieval quality but consume more memory. The system therefore supports environment-based model selection and a graceful lexical fallback.

### Explainability vs latency

The workflow keeps policy evidence, citations, validation, and trace information rather than returning only a final label. This increases processing time but makes the result inspectable.

### Generality vs policy specificity

The agent interfaces are generic enough to support structured claim cases, while the policy retrieval and decision logic are grounded in the supplied policy document.

### Simplicity vs scale

The current 34-chunk policy index is intentionally simple and reproducible. A production deployment with thousands of documents would require persistent indexing, versioning, metadata filtering, and stronger retrieval infrastructure.

---

## 17. Submission Checklist

- [x] Public GitHub repository
- [x] Policy PDF ingestion
- [x] Meaningful chunks with page/section metadata
- [x] Dense + sparse retrieval
- [x] RRF fusion
- [x] Reranking with fallback
- [x] At least 3 specialized agents
- [x] Structured agent state
- [x] Machine-readable final decision
- [x] Policy citations
- [x] NEEDS_REVIEW / abstention
- [x] FastAPI API
- [x] Streamlit frontend
- [x] Visible agent trace
- [x] 12 supplied public cases evaluated
- [x] 10 additional cases evaluated
- [x] At least 2 NEEDS_REVIEW cases
- [x] Failure analysis
- [x] Local reproducibility
- [ ] Final verified live frontend URL
- [ ] Final verified live API URL

---

## 18. Author

**Shaikh Rayyan Ahmed**

AI / Full Stack Developer

GitHub: `RayyanStudiosTM`

