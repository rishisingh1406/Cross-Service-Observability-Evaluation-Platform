import time
from uuid import uuid4

import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, make_asgi_app

from otel_common.tracing import configure_tracing


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Cross-Service AI Observability - Gateway",
    version="1.0.0",
)


# ============================================================
# PROMETHEUS METRICS
# ============================================================

gateway_requests_total = Counter(
    "gateway_requests_total",
    "Total number of gateway requests",
    ["route"],
)

gateway_request_duration_seconds = Histogram(
    "gateway_request_duration_seconds",
    "Gateway request latency in seconds",
    ["route"],
)


# Expose Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    request_id: str
    prompt_version: str


# ============================================================
# OPEN TELEMETRY
# ============================================================

configure_tracing(
    service_name="gateway",
    app=app,
)


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "gateway",
    }


# ============================================================
# CHAT
# ============================================================


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    start_time = time.perf_counter()

    try:

        request_id = str(uuid4())

        async with httpx.AsyncClient() as client:

            response = await client.post(
                "http://agent:8001/execute",
                json={
                    "user_id": request.user_id,
                    "message": request.message,
                },
                timeout=10.0,
            )

        response.raise_for_status()

        agent_result = response.json()

        return ChatResponse(
            answer=agent_result["result"],
            request_id=request_id,
            prompt_version="v1",
        )

    finally:

        gateway_requests_total.labels(
            route="/chat"
        ).inc()

        gateway_request_duration_seconds.labels(
            route="/chat"
        ).observe(
            time.perf_counter() - start_time
        )