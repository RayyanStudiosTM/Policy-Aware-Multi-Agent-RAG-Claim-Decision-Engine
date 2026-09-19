FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN python scripts/ingest_policy.py
EXPOSE 8000
CMD ["uvicorn","backend.api.main:app","--host","0.0.0.0","--port","8000"]
