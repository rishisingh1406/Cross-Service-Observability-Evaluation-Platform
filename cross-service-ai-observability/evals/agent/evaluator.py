from dataclasses import dataclass


@dataclass
class TraceEvidence:
    """
    Minimal representation of the evidence we need
    from an agent execution trace.
    """

    route: str

    retrieval_called: bool
    memory_called: bool
    llm_called: bool


@dataclass
class EvaluationResult:
    """
    Result of evaluating one routing case.
    """

    case_name: str

    route_correct: bool
    retrieval_correct: bool
    memory_correct: bool
    llm_correct: bool

    passed: bool

    failures: list[str]


def evaluate_trace(
    *,
    case,
    trace: TraceEvidence,
) -> EvaluationResult:

    failures: list[str] = []

    # ========================================================
    # ROUTING DECISION
    # ========================================================

    route_correct = (
        trace.route == case.expected_route
    )

    if not route_correct:
        failures.append(
            (
                f"Expected route "
                f"'{case.expected_route}', "
                f"got '{trace.route}'"
            )
        )

    # ========================================================
    # RETRIEVAL EXECUTION
    # ========================================================

    retrieval_correct = (
        trace.retrieval_called
        == case.retrieval_expected
    )

    if not retrieval_correct:
        failures.append(
            (
                "Retrieval execution mismatch: "
                f"expected "
                f"{case.retrieval_expected}, "
                f"got "
                f"{trace.retrieval_called}"
            )
        )

    # ========================================================
    # MEMORY EXECUTION
    # ========================================================

    memory_correct = (
        trace.memory_called
        == case.memory_expected
    )

    if not memory_correct:
        failures.append(
            (
                "Memory execution mismatch: "
                f"expected "
                f"{case.memory_expected}, "
                f"got "
                f"{trace.memory_called}"
            )
        )

    # ========================================================
    # LLM EXECUTION
    # ========================================================

    llm_correct = (
        trace.llm_called
        == case.llm_expected
    )

    if not llm_correct:
        failures.append(
            (
                "LLM execution mismatch: "
                f"expected "
                f"{case.llm_expected}, "
                f"got "
                f"{trace.llm_called}"
            )
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    passed = len(failures) == 0

    return EvaluationResult(
        case_name=case.name,
        route_correct=route_correct,
        retrieval_correct=retrieval_correct,
        memory_correct=memory_correct,
        llm_correct=llm_correct,
        passed=passed,
        failures=failures,
    )