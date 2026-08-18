FROM python:3.11-slim

WORKDIR /app

COPY services/memory/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/memory/main.py .

COPY libs ./libs

ENV PYTHONPATH=/app/libs

RUN mkdir -p /data

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]