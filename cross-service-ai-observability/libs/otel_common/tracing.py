import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracing(
    service_name: str,
    app,
) -> None:

    # ============================================================
    # RESOURCE
    # ============================================================

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": "development",
        }
    )

    # ============================================================
    # TRACE PROVIDER
    # ============================================================

    provider = TracerProvider(
        resource=resource
    )

    # ============================================================
    # OTLP EXPORTER
    # ============================================================

    otlp_endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4317",
    )

    exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,
    )

    # ============================================================
    # SPAN PROCESSOR
    # ============================================================

    provider.add_span_processor(
        BatchSpanProcessor(exporter)
    )

    trace.set_tracer_provider(provider)

    # ============================================================
    # FASTAPI INSTRUMENTATION
    # ============================================================
    #
    # Prometheus continuously calls /metrics.
    #
    # We do NOT want those monitoring requests appearing
    # as application traces.
    #
    # This keeps our traces focused on actual application
    # traffic:
    #
    # gateway → agent → retrieval/memory → llm
    #
    # ============================================================

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="/metrics",
    )

    # ============================================================
    # HTTPX INSTRUMENTATION
    # ============================================================

    HTTPXClientInstrumentor().instrument()