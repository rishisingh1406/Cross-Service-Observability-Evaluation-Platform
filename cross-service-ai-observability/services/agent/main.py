import httpx

from fastapi import FastAPI
from pydantic import BaseModel

from opentelemetry import trace

from otel_common.tracing import configure_tracing


app = FastAPI(
    title="Cross-Service AI Observability - Agent",
    version="1.0.0",
)


class ExecuteRequest(BaseModel):
    user_id: str
    message: str


class ExecuteResponse(BaseModel):
    result: str
    service: str


configure_tracing(
    service_name="agent-service",
    app=app,
)


tracer = trace.get_tracer("agent-service")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "agent-service",
    }


@app.post("/execute", response_model=ExecuteResponse)
async def execute(request: ExecuteRequest):

    with tracer.start_as_current_span("agent.execute") as span:

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://retrieval:8002/search",
                json={
                    "query": request.message,
                    "top_k": 3,
                },
                timeout=10.0,
            )

        response.raise_for_status()

        retrieval_data = response.json()
        results = retrieval_data["results"]

        span.set_attribute(
            "agent.retrieval.result_count",
            len(results),
        )

        answer = (
            f"Agent processed: {request.message}. "
            f"Retrieved {len(results)} relevant documents."
        )

        return ExecuteResponse(
            result=answer,
            service="agent-service",
        )