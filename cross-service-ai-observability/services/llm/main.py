from fastapi import FastAPI
from pydantic import BaseModel

from opentelemetry import trace
from otel_common.tracing import configure_tracing


app = FastAPI(
    title="Cross-Service AI Observability - LLM",
    version="1.0.0",
)


class GenerateRequest(BaseModel):
    user_id: str
    prompt: str


class GenerateResponse(BaseModel):
    response: str
    provider: str
    service: str


class MockProvider:
    name = "mock"

    def generate(self, prompt: str) -> str:
        return (
            f"Mock LLM response for: {prompt}"
        )


configure_tracing(
    service_name="llm-service",
    app=app,
)


tracer = trace.get_tracer("llm-service")

provider = MockProvider()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "llm-service",
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):

    with tracer.start_as_current_span("llm.generate") as span:

        span.set_attribute(
            "llm.provider",
            provider.name,
        )

        span.set_attribute(
            "llm.prompt_length",
            len(request.prompt),
        )

        with tracer.start_as_current_span(
            "llm.provider.generate"
        ) as provider_span:

            provider_span.set_attribute(
                "llm.provider.name",
                provider.name,
            )

            response = provider.generate(
                request.prompt
            )

            provider_span.set_attribute(
                "llm.response_length",
                len(response),
            )

        return GenerateResponse(
            response=response,
            provider=provider.name,
            service="llm-service",
        )
