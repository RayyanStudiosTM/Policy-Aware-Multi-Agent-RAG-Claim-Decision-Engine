# Evaluation Results — Policy-Aware Multi-Agent RAG Claim Decision Engine

## Final evaluation command

```bash
python scripts/evaluate.py --timeout 300
```

The final completed run was executed locally against:

```text
http://127.0.0.1:8000
```

The backend health check returned:

```json
{
  "status": "ok",
  "service": "aptino-claim-engine"
}
```

## Public cases

| Metric | Result |
|---|---:|
| Total | 12 |
| Successful | 12 |
| Failed | 0 |
| Validation PASS | 12 |
| NEEDS_REVIEW | 2 |
| Average duration | 72.47 s |

### Decision distribution

| Decision | Cases |
|---|---:|
| ADMISSIBLE_WITH_LIMITS | 3 |
| NOT_ADMISSIBLE | 4 |
| ADMISSIBLE | 3 |
| NEEDS_REVIEW | 2 |

### NEEDS_REVIEW

- `PUB-006`
- `PUB-011`

## Custom cases

| Metric | Result |
|---|---:|
| Total | 10 |
| Successful | 10 |
| Failed | 0 |
| Validation PASS | 10 |
| NEEDS_REVIEW | 1 |
| Average duration | 71.12 s |

### Decision distribution

| Decision | Cases |
|---|---:|
| ADMISSIBLE_WITH_LIMITS | 4 |
| ADMISSIBLE | 3 |
| NOT_ADMISSIBLE | 2 |
| NEEDS_REVIEW | 1 |

### NEEDS_REVIEW

- `CUSTOM-006`

## Overall

| Metric | Result |
|---|---:|
| Total cases | 22 |
| Successful | 22 |
| Failed | 0 |
| NEEDS_REVIEW | 3 |
| Public | 12/12 |
| Custom | 10/10 |
| Validation PASS | 22/22 |

## Custom case coverage

The ten custom cases cover:

1. Room + ambulance sub-limits
2. Waiting period
3. Insufficient evidence
4. Experimental treatment exclusion
5. Pre-existing condition
6. Outpatient coverage boundary
7. Multiple policy sections
8. Irrelevant attributes
9. Uncertain/incomplete condition
10. Multiple limits and numerical deductions

## Performance

The final run averaged approximately 71–72 seconds per claim.

This is the main performance limitation of the current multi-agent architecture. The system prioritizes evidence retrieval, policy citations, structured validation, and an inspectable trace.

## Observed engineering failures and improvements

### Evaluation timeout

An earlier evaluation using a shorter/default timeout did not finish all public cases. The final run used:

```text
--timeout 300
```

and completed all 22 cases successfully.

### Render memory pressure

The initial 512 MiB Render deployment exceeded the available memory during startup.

The mitigation is:

```text
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
USE_CROSS_ENCODER=false
```

plus limited thread parallelism and the lexical reranking fallback.

### Model download reliability

A reranker model download previously encountered DNS/network resolution problems. The retrieval implementation therefore supports a lexical reranking fallback instead of making the cross-encoder an unconditional startup dependency.

## Reproducibility

The evaluator writes:

```text
evaluation/public_results.json
evaluation/custom_results.json
evaluation/evaluation_summary.json
```

The final summary is:

```json
{
  "total_cases": 22,
  "total_successful": 22,
  "total_failed": 0,
  "total_needs_review": 3
}
```

