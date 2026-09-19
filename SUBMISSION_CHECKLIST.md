# Aptino Submission Checklist

- [x] Policy PDF indexed with page/section/chunk metadata
- [x] Dense retrieval + sparse BM25 + RRF + reranking architecture
- [x] Five specialized agents with typed state
- [x] Structured `/analyze` response
- [x] Citation metadata and validation agent
- [x] `NEEDS_REVIEW` abstention for unresolved evidence
- [x] FastAPI `/health` and `/analyze`
- [x] Streamlit reviewer UI
- [x] All 12 supplied public cases evaluated
- [x] Five additional candidate cases evaluated
- [x] Two+ NEEDS_REVIEW cases present in evaluation
- [x] Three failure modes documented
- [x] Reproducible evaluation command
- [x] Dockerfile and Render configuration included
- [ ] Deploy API and frontend and add live URLs to README before final submission
- [ ] Push repository to GitHub before final submission

## Local verification

```bash
python scripts/ingest_policy.py
python evaluation/evaluate.py
pytest -q
```

The included deterministic run reaches exact decision-label agreement on the 12 public cases and records citation/page retrieval metrics. Model-backed retrieval can be enabled by installing/caching the SentenceTransformers models listed in `requirements.txt`.
