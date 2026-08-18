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

            # --------------------------------------------------
            # 1. Retrieval
            # --------------------------------------------------

            retrieval_response = await client.post(
                "http://retrieval:8002/search",
                json={
                    "query": request.message,
                    "top_k": 3,
                },
                timeout=10.0,
            )

            retrieval_response.raise_for_status()

            retrieval_data = retrieval_response.json()
            results = retrieval_data["results"]

            span.set_attribute(
                "agent.retrieval.result_count",
                len(results),
            )

            # --------------------------------------------------
            # 2. Memory
            # --------------------------------------------------

            memory_response = await client.post(
                "http://memory:8003/memory",
                json={
                    "user_id": request.user_id,
                    "content": request.message,
                },
                timeout=10.0,
            )

            memory_response.raise_for_status()

            memory_data = memory_response.json()

            span.set_attribute(
                "agent.memory.id",
                memory_data["id"],
            )

            # --------------------------------------------------
            # 3. LLM
            # --------------------------------------------------

            llm_prompt = (
                f"User question: {request.message}\n\n"
                f"Retrieved context: {results}\n\n"
                f"Use the context to answer the user."
            )

            llm_response = await client.post(
                "http://llm:8004/generate",
                json={
                    "user_id": request.user_id,
                    "prompt": llm_prompt,
                },
                timeout=10.0,
            )

            llm_response.raise_for_status()

            llm_data = llm_response.json()

            span.set_attribute(
                "agent.llm.provider",
                llm_data["provider"],
            )

        # ------------------------------------------------------
        # Final result
        # ------------------------------------------------------

        answer = (
            f"{llm_data['response']} "
            f"(Retrieved {len(results)} relevant documents.)"
        )

        return ExecuteResponse(
            result=answer,
            service="agent-service",
        )