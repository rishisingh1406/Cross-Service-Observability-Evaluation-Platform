FROM python:3.11-slim

WORKDIR /app

COPY services/gateway/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/gateway /app
COPY libs/otel_common /app/otel_common

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]