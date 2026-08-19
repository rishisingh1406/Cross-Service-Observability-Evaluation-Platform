from fastapi import FastAPI
from pydantic import BaseModel

from opentelemetry import trace
from otel_common.tracing import configure_tracing


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Cross-Service AI Observability - LLM",
    version="1.0.0",
)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_NAME = "mock-v1"


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================


class GenerateRequest(BaseModel):
    user_id: str
    prompt: str


class GenerateResponse(BaseModel):
    response: str
    provider: str
    model: str
    service: str


# ============================================================
# MOCK PROVIDER
# ============================================================


class MockProvider:

    name = "mock"

    def generate(self, prompt: str) -> str:
        return (
            f"Mock LLM response for: {prompt}"
        )


# ============================================================
# OPEN TELEMETRY
# ============================================================

configure_tracing(
    service_name="llm-service",
    app=app,
)


tracer = trace.get_tracer(
    "llm-service"
)


provider = MockProvider()


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "llm-service",
        "provider": provider.name,
        "model": MODEL_NAME,
    }


# ============================================================
# GENERATE
# ============================================================


@app.post(
    "/generate",
    response_model=GenerateResponse,
)
async def generate(
    request: GenerateRequest,
):

    with tracer.start_as_current_span(
        "llm.generate"
    ) as span:

        # ----------------------------------------------------
        # PROVIDER / MODEL METADATA
        # ----------------------------------------------------

        span.set_attribute(
            "llm.provider",
            provider.name,
        )

        span.set_attribute(
            "llm.model",
            MODEL_NAME,
        )

        span.set_attribute(
            "llm.prompt_length",
            len(request.prompt),
        )

        # ----------------------------------------------------
        # PROVIDER EXECUTION
        # ----------------------------------------------------

        with tracer.start_as_current_span(
            "llm.provider.generate"
        ) as provider_span:

            provider_span.set_attribute(
                "llm.provider.name",
                provider.name,
            )

            provider_span.set_attribute(
                "llm.model",
                MODEL_NAME,
            )

            response = provider.generate(
                request.prompt
            )

            provider_span.set_attribute(
                "llm.response_length",
                len(response),
            )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return GenerateResponse(
            response=response,
            provider=provider.name,
            model=MODEL_NAME,
            service="llm-service",
        )