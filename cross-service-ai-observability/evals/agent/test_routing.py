from evals.agent.cases import ROUTING_CASES
from evals.agent.evaluator import (
    TraceEvidence,
    evaluate_trace,
)


def test_routing_cases():

    for case in ROUTING_CASES:

        # ----------------------------------------------------
        # Temporary synthetic trace.
        #
        # This is ONLY to verify that our evaluator itself
        # works before connecting it to real traces.
        # ----------------------------------------------------

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