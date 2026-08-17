from uuid import uuid4

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from otel_common.tracing import configure_tracing


app = FastAPI(
    title="Cross-Service AI Observability - Gateway",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    request_id: str
    prompt_version: str


configure_tracing(
    service_name="gateway",
    app=app,
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "gateway",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
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