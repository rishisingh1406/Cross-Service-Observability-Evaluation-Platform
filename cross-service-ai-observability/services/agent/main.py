import json
import time
from pathlib import Path

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from opentelemetry import trace
from prometheus_client import (
    Counter,
    Histogram,
    make_asgi_app,
)

from otel_common.tracing import configure_tracing


# ============================================================
# PROJECT / PROMPT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

PROMPT_REGISTRY_PATH = (
    PROJECT_ROOT / "prompts" / "registry.json"
)

with open(
    PROMPT_REGISTRY_PATH,
    "r",
    encoding="utf-8",
) as f:
    PROMPT_REGISTRY = json.load(f)


AGENT_PROMPT_VERSION = (
    PROMPT_REGISTRY["agent"]["version"]
)

AGENT_PROMPT_PATH = (
    PROJECT_ROOT
    / PROMPT_REGISTRY["agent"]["prompt_path"]
)

with open(
    AGENT_PROMPT_PATH,
    "r",
    encoding="utf-8",
) as f:
    AGENT_SYSTEM_PROMPT = f.read()


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Cross-Service AI Observability - Agent",
    version="1.0.0",
)


# ============================================================
# PROMETHEUS METRICS
# ============================================================

agent_requests_total = Counter(
    "agent_requests_total",
    "Total number of agent execution requests",
    ["route"],
)

agent_request_duration_seconds = Histogram(
    "agent_request_duration_seconds",
    "Agent execution latency in seconds",
    ["route"],
)

agent_llm_requests_total = Counter(
    "agent_llm_requests_total",
    "Total number of LLM requests made by the agent",
    ["model"],
)

agent_retrieval_requests_total = Counter(
    "agent_retrieval_requests_total",
    "Total number of retrieval requests made by the agent",
)

agent_memory_requests_total = Counter(
    "agent_memory_requests_total",
    "Total number of memory requests made by the agent",
)


# Expose Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================


class ExecuteRequest(BaseModel):
    user_id: str
    message: str


class ExecuteResponse(BaseModel):
    result: str
    service: str
    prompt_version: str
    model: str | None = None


# ============================================================
# OPEN TELEMETRY
# ============================================================

configure_tracing(
    service_name="agent-service",
    app=app,
)

tracer = trace.get_tracer(
    "agent-service"
)


# ============================================================
# ROUTING
# ============================================================


def determine_route(message: str) -> str:
    """
    Determine which execution path the agent should take.

    Routes:

    - retrieval:
        Knowledge / policy / technical questions.

    - memory:
        Requests referring to previous conversations
        or stored user information.

    - direct:
        Simple conversational requests.
    """

    text = message.lower().strip()

    retrieval_keywords = [
        "policy",
        "policies",
        "architecture",
        "distributed system",
        "distributed systems",
        "observability",
        "retrieval",
        "rag",
        "agent",
        "agents",
        "open telemetry",
        "opentelemetry",
        "how does",
        "explain",
        "documentation",
        "knowledge",
    ]

    memory_keywords = [
        "remember",
        "previous",
        "earlier",
        "last time",
        "we discussed",
        "my preference",
        "my preferences",
        "what did i tell you",
        "what do you know about me",
    ]

    if any(
        keyword in text
        for keyword in memory_keywords
    ):
        return "memory"

    if any(
        keyword in text
        for keyword in retrieval_keywords
    ):
        return "retrieval"

    return "direct"


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "agent-service",
        "prompt_version": AGENT_PROMPT_VERSION,
    }


# ============================================================
# EXECUTE
# ============================================================


@app.post(
    "/execute",
    response_model=ExecuteResponse,
)
async def execute(
    request: ExecuteRequest,
):

    # Determine route before starting the main operation
    # so that Prometheus can record the correct route even
    # if an exception occurs later.
    route = determine_route(
        request.message
    )

    start_time = time.perf_counter()

    try:

        with tracer.start_as_current_span(
            "agent.execute"
        ) as span:

            # ====================================================
            # PROMPT METADATA
            # ====================================================

            span.set_attribute(
                "agent.prompt.version",
                AGENT_PROMPT_VERSION,
            )

            span.set_attribute(
                "agent.prompt.path",
                PROMPT_REGISTRY["agent"]["prompt_path"],
            )

            # ====================================================
            # ROUTING
            # ====================================================

            span.set_attribute(
                "agent.routing.route",
                route,
            )

            span.set_attribute(
                "agent.routing.message_length",
                len(request.message),
            )

            # These attributes are used by the Day 77
            # routing evaluation suite.

            span.set_attribute(
                "agent.routing.retrieval_expected",
                route == "retrieval",
            )

            span.set_attribute(
                "agent.routing.memory_expected",
                route == "memory",
            )

            span.set_attribute(
                "agent.routing.direct_expected",
                route == "direct",
            )

            results = []
            memory_data = None
            llm_data = None

            # ====================================================
            # HTTP CLIENT
            # ====================================================

            async with httpx.AsyncClient() as client:

                # =================================================
                # RETRIEVAL ROUTE
                # =================================================

                if route == "retrieval":

                    with tracer.start_as_current_span(
                        "agent.route.retrieval"
                    ) as route_span:

                        route_span.set_attribute(
                            "agent.route",
                            "retrieval",
                        )

                        retrieval_response = (
                            await client.post(
                                "http://retrieval:8002/search",
                                json={
                                    "query": request.message,
                                    "top_k": 3,
                                },
                                timeout=10.0,
                            )
                        )

                        retrieval_response.raise_for_status()

                        retrieval_data = (
                            retrieval_response.json()
                        )

                        results = (
                            retrieval_data["results"]
                        )

                        agent_retrieval_requests_total.inc()

                        span.set_attribute(
                            "agent.retrieval.called",
                            True,
                        )

                        span.set_attribute(
                            "agent.retrieval.result_count",
                            len(results),
                        )

                else:

                    span.set_attribute(
                        "agent.retrieval.called",
                        False,
                    )

                # =================================================
                # MEMORY ROUTE
                # =================================================

                if route == "memory":

                    with tracer.start_as_current_span(
                        "agent.route.memory"
                    ) as route_span:

                        route_span.set_attribute(
                            "agent.route",
                            "memory",
                        )

                        memory_response = (
                            await client.post(
                                "http://memory:8003/memory",
                                json={
                                    "user_id": request.user_id,
                                    "content": request.message,
                                },
                                timeout=10.0,
                            )
                        )

                        memory_response.raise_for_status()

                        memory_data = (
                            memory_response.json()
                        )

                        agent_memory_requests_total.inc()

                        span.set_attribute(
                            "agent.memory.called",
                            True,
                        )

                        span.set_attribute(
                            "agent.memory.id",
                            memory_data["id"],
                        )

                else:

                    span.set_attribute(
                        "agent.memory.called",
                        False,
                    )

                # =================================================
                # BUILD VERSIONED LLM PROMPT
                # =================================================

                llm_prompt = AGENT_SYSTEM_PROMPT.format(
                    user_message=request.message,
                    retrieved_context=results,
                    memory=memory_data,
                )

                # =================================================
                # LLM ROUTE
                # =================================================

                with tracer.start_as_current_span(
                    "agent.route.llm"
                ) as route_span:

                    route_span.set_attribute(
                        "agent.route",
                        route,
                    )

                    route_span.set_attribute(
                        "agent.prompt.version",
                        AGENT_PROMPT_VERSION,
                    )

                    llm_response = (
                        await client.post(
                            "http://llm:8004/generate",
                            json={
                                "user_id": request.user_id,
                                "prompt": llm_prompt,
                            },
                            timeout=10.0,
                        )
                    )

                    llm_response.raise_for_status()

                    llm_data = (
                        llm_response.json()
                    )

                    span.set_attribute(
                        "agent.llm.called",
                        True,
                    )

                    span.set_attribute(
                        "agent.llm.provider",
                        llm_data.get(
                            "provider",
                            "unknown",
                        ),
                    )

                    # ------------------------------------------------
                    # MODEL METADATA
                    # ------------------------------------------------

                    model_name = llm_data.get(
                        "model"
                    )

                    if model_name:

                        span.set_attribute(
                            "agent.llm.model",
                            model_name,
                        )

                        agent_llm_requests_total.labels(
                            model=model_name
                        ).inc()

                    else:

                        agent_llm_requests_total.labels(
                            model="unknown"
                        ).inc()

            # ====================================================
            # FINAL RESPONSE
            # ====================================================

            answer = llm_data["response"]

            return ExecuteResponse(
                result=answer,
                service="agent-service",
                prompt_version=AGENT_PROMPT_VERSION,
                model=llm_data.get("model"),
            )

    finally:

        # ========================================================
        # PROMETHEUS REQUEST METRICS
        # ========================================================

        agent_requests_total.labels(
            route=route
        ).inc()

        agent_request_duration_seconds.labels(
            route=route
        ).observe(
            time.perf_counter() - start_time
        )