FROM python:3.11-slim

WORKDIR /app

COPY services/llm/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/llm/main.py .
COPY libs ./libs

ENV PYTHONPATH=/app/libs

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]