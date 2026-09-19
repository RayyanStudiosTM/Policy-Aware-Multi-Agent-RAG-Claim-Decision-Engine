install:
	pip install -r requirements.txt
ingest:
	python scripts/ingest_policy.py
api:
	uvicorn backend.api.main:app --reload --port 8000
ui:
	streamlit run frontend/app.py
eval:
	python evaluation/evaluate.py
test:
	pytest -q
