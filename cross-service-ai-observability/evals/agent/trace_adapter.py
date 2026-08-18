from dataclasses import dataclass


@dataclass
class TraceEvidence:
    """
    Evidence extracted from an actual agent execution.

    This represents what actually happened, not what the
    agent was expected to do.
    """

    route: str

    retrieval_called: bool
    memory_called: bool
    llm_called: bool


def evidence_from_agent_response(
    *,
    route: str,
    retrieval_called: bool,
    memory_called: bool,
    llm_called: bool,
) -> TraceEvidence:
    """
    Convert actual execution evidence into the structure
    consumed by the routing evaluator.

    In the next phase this adapter can be populated directly
    from OpenTelemetry spans.
    """

    return TraceEvidence(
        route=route,
        retrieval_called=retrieval_called,
        memory_called=memory_called,
        llm_called=llm_called,
    )
