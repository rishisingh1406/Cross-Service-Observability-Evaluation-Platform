import pytest

from evals.agent.cases import ROUTING_CASES
from evals.agent.evaluator import (
    TraceEvidence,
    evaluate_trace,
)


@pytest.mark.parametrize(
    "case",
    ROUTING_CASES,
    ids=lambda case: case.name,
)
def test_routing_case(case):

    # Temporary synthetic trace.
    #
    # This verifies that the evaluator correctly evaluates
    # routing decisions and tool usage.
    #
    # Later this will be replaced by actual OpenTelemetry
    # trace evidence.

    trace = TraceEvidence(
        route=case.expected_route,
        retrieval_called=case.retrieval_expected,
        memory_called=case.memory_expected,
        llm_called=case.llm_expected,
    )

    result = evaluate_trace(
        case=case,
        trace=trace,
    )

    assert result.passed, (
        f"{case.name} failed: "
        f"{result.failures}"
    )