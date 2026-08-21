import os
import sqlite3
import time

from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_client import Histogram, make_asgi_app
from opentelemetry import trace
from otel_common.tracing import configure_tracing


app = FastAPI(
    title="Cross-Service AI Observability - Memory",
    version="1.0.0",
)


class MemoryRequest(BaseModel):
    user_id: str
    content: str


class MemoryResponse(BaseModel):
    id: int
    user_id: str
    content: str
    service: str


configure_tracing(
    service_name="memory-service",
    app=app,
)

tracer = trace.get_tracer("memory-service")


memory_latency_seconds = Histogram(
    "memory_latency_seconds",
    "Memory service request latency in seconds",
    ["operation"],
)


DB_PATH = os.getenv(
    "MEMORY_DB_PATH",
    "/data/memory.db",
)


def initialize_database():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL
            )
            """
        )
        connection.commit()


initialize_database()


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "memory-service",
    }


@app.post("/memory", response_model=MemoryResponse)
async def create_memory(request: MemoryRequest):
    start_time = time.perf_counter()

    try:
        with tracer.start_as_current_span("memory.store") as span:
            span.set_attribute(
                "memory.user_id",
                request.user_id,
            )

            span.set_attribute(
                "memory.content_length",
                len(request.content),
            )

            # Day 81 recovery:
            # Artificial latency removed.
            # The database operation should now be
            # the primary work inside this span.

            with tracer.start_as_current_span(
                "memory.database.insert"
            ) as db_span:
                with sqlite3.connect(DB_PATH) as connection:
                    cursor = connection.execute(
                        """
                        INSERT INTO memories (user_id, content)
                        VALUES (?, ?)
                        """,
                        (
                            request.user_id,
                            request.content,
                        ),
                    )

                    connection.commit()
                    memory_id = cursor.lastrowid

                db_span.set_attribute(
                    "db.system",
                    "sqlite",
                )

                db_span.set_attribute(
                    "db.operation.name",
                    "INSERT",
                )

            return MemoryResponse(
                id=memory_id,
                user_id=request.user_id,
                content=request.content,
                service="memory-service",
            )

    finally:
        memory_latency_seconds.labels(
            operation="write"
        ).observe(
            time.perf_counter() - start_time
        )


@app.get("/memory")
async def get_memories(user_id: str):
    start_time = time.perf_counter()

    try:
        with tracer.start_as_current_span(
            "memory.retrieve"
        ) as span:
            span.set_attribute(
                "memory.user_id",
                user_id,
            )

            with tracer.start_as_current_span(
                "memory.database.select"
            ) as db_span:
                with sqlite3.connect(DB_PATH) as connection:
                    cursor = connection.execute(
                        """
                        SELECT id, user_id, content
                        FROM memories
                        WHERE user_id = ?
                        ORDER BY id DESC
                        """,
                        (user_id,),
                    )

                    rows = cursor.fetchall()

                db_span.set_attribute(
                    "db.system",
                    "sqlite",
                )

                db_span.set_attribute(
                    "db.operation.name",
                    "SELECT",
                )

            return {
                "memories": [
                    {
                        "id": row[0],
                        "user_id": row[1],
                        "content": row[2],
                    }
                    for row in rows
                ],
                "service": "memory-service",
            }

    finally:
        memory_latency_seconds.labels(
            operation="read"
        ).observe(
            time.perf_counter() - start_time
        )