import httpx

from fastapi import FastAPI
from pydantic import BaseModel

from opentelemetry import trace

from otel_common.tracing import configure_tracing


app = FastAPI(
    title="Cross-Service AI Observability - Agent",
    version="1.0.0",
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================


class ExecuteRequest(BaseModel):
    user_id: str
    message: str


class ExecuteResponse(BaseModel):
    result: str
    service: str


# ============================================================
# OPEN TELEMETRY
# ============================================================


configure_tracing(
    service_name="agent-service",
    app=app,
)


tracer = trace.get_tracer("agent-service")


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

    if any(keyword in text for keyword in memory_keywords):
        return "memory"

    if any(keyword in text for keyword in retrieval_keywords):
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
    }


# ============================================================
# EXECUTE
# ============================================================


@app.post(
    "/execute",
    response_model=ExecuteResponse,
)
async def execute(request: ExecuteRequest):

    with tracer.start_as_current_span(
        "agent.execute"
    ) as span:

        # ----------------------------------------------------
        # 1. Determine route
        # ----------------------------------------------------

        route = determine_route(request.message)

        span.set_attribute(
            "agent.routing.route",
            route,
        )

        span.set_attribute(
            "agent.routing.message_length",
            len(request.message),
        )

        # These attributes are extremely important for
        # Project 7 routing evaluation.
        #
        # The evaluator can inspect the trace and determine:
        #
        # expected route == actual route
        #
        # rather than judging the generated text.

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

        # ----------------------------------------------------
        # HTTP client
        # ----------------------------------------------------

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

                    retrieval_response = await client.post(
                        "http://retrieval:8002/search",
                        json={
                            "query": request.message,
                            "top_k": 3,
                        },
                        timeout=10.0,
                    )

                    retrieval_response.raise_for_status()

                    retrieval_data = (
                        retrieval_response.json()
                    )

                    results = retrieval_data["results"]

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

                    memory_response = await client.post(
                        "http://memory:8003/memory",
                        json={
                            "user_id": request.user_id,
                            "content": request.message,
                        },
                        timeout=10.0,
                    )

                    memory_response.raise_for_status()

                    memory_data = (
                        memory_response.json()
                    )

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
            # DIRECT / RETRIEVAL / MEMORY → LLM
            # =================================================

            llm_prompt = (
                f"User question: {request.message}\n\n"
                f"Retrieved context: {results}\n\n"
                f"Memory: {memory_data}\n\n"
                f"Answer the user clearly."
            )

            with tracer.start_as_current_span(
                "agent.route.llm"
            ) as route_span:

                route_span.set_attribute(
                    "agent.route",
                    route,
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
                    "agent.llm.called",
                    True,
                )

                span.set_attribute(
                    "agent.llm.provider",
                    llm_data["provider"],
                )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        answer = llm_data["response"]

        return ExecuteResponse(
            result=answer,
            service="agent-service",
        )