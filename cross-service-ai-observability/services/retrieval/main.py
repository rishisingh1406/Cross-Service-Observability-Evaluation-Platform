import time
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from opentelemetry import trace
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    make_asgi_app,
)

from otel_common.tracing import configure_tracing

from retriever import BM25Retriever


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Cross-Service AI Observability - Retrieval",
    version="1.0.0",
)


# ============================================================
# PROMETHEUS METRICS
# ============================================================

retrieval_requests_total = Counter(
    "retrieval_requests_total",
    "Total number of retrieval requests",
)

retrieval_request_duration_seconds = Histogram(
    "retrieval_request_duration_seconds",
    "Retrieval request latency in seconds",
)

retrieval_results_returned = Histogram(
    "retrieval_results_returned",
    "Number of documents returned by retrieval",
)

retrieval_top_score = Histogram(
    "retrieval_top_score",
    "Top retrieval score",
)

retrieval_document_count = Gauge(
    "retrieval_document_count",
    "Number of documents in the retrieval index",
)


# Expose Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class SearchResult(BaseModel):
    document: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]


# ============================================================
# OPEN TELEMETRY
# ============================================================

configure_tracing(
    service_name="retrieval-service",
    app=app,
)


# ============================================================
# RETRIEVER
# ============================================================

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

retriever = BM25Retriever(
    knowledge_dir=str(KNOWLEDGE_DIR)
)


tracer = trace.get_tracer(
    "retrieval-service"
)


# Record the current number of indexed documents.
retrieval_document_count.set(
    retriever.document_count
)


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "retrieval-service",
        "document_count": retriever.document_count,
    }


# ============================================================
# SEARCH
# ============================================================


@app.post(
    "/search",
    response_model=SearchResponse,
)
async def search(
    request: SearchRequest,
):

    start_time = time.perf_counter()

    results = []
    top_score = 0.0

    try:

        with tracer.start_as_current_span(
            "retrieval.search"
        ) as span:

            # =================================================
            # BM25 SEARCH
            # =================================================

            results = retriever.search(
                request.query,
                top_k=request.top_k,
            )

            top_score = (
                results[0]["score"]
                if results
                else 0.0
            )

            # =================================================
            # OPEN TELEMETRY ATTRIBUTES
            # =================================================

            span.set_attribute(
                "retrieval.doc_count",
                retriever.document_count,
            )

            span.set_attribute(
                "retrieval.result_count",
                len(results),
            )

            span.set_attribute(
                "retrieval.top_k",
                request.top_k,
            )

            span.set_attribute(
                "retrieval.top_score",
                float(top_score),
            )

            span.set_attribute(
                "retrieval.index_type",
                "bm25",
            )

            # =================================================
            # RESPONSE
            # =================================================

            return SearchResponse(
                results=results,
            )

    finally:

        # =====================================================
        # PROMETHEUS METRICS
        # =====================================================

        retrieval_requests_total.inc()

        retrieval_request_duration_seconds.observe(
            time.perf_counter() - start_time
        )

        retrieval_results_returned.observe(
            len(results)
        )

        retrieval_top_score.observe(
            float(top_score)
        )

        retrieval_document_count.set(
            retriever.document_count
        )