FROM python:3.12-slim

WORKDIR /app

COPY services/retrieval/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY libs ./libs
COPY services/retrieval ./services/retrieval

ENV PYTHONPATH=/app/libs:/app/services/retrieval

WORKDIR /app/services/retrieval

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]