from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from otel_common.tracing import configure_tracing
from opentelemetry import trace

from retriever import BM25Retriever


app = FastAPI(
    title="Cross-Service AI Observability - Retrieval",
    version="1.0.0",
)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class SearchResult(BaseModel):
    document: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]


configure_tracing(
    service_name="retrieval-service",
    app=app,
)


KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

retriever = BM25Retriever(
    knowledge_dir=str(KNOWLEDGE_DIR)
)


tracer = trace.get_tracer("retrieval-service")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "retrieval-service",
        "document_count": retriever.document_count,
    }


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    with tracer.start_as_current_span("retrieval.search") as span:



        results = retriever.search(
            request.query,
            top_k=request.top_k,
        )

        top_score = (
            results[0]["score"]
            if results
            else 0.0
        )

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

        return SearchResponse(
            results=results,
        )