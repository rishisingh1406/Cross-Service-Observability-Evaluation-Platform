from dataclasses import dataclass


@dataclass(frozen=True)
class PromptEvaluationResult:
    case_name: str
    passed: bool
    failure: str | None = None


def evaluate_prompt_case(
    case,
    prompt: str,
) -> PromptEvaluationResult:

    prompt_lower = prompt.lower()

    if case.expected_behavior == "cite_policy_sources":

        required_terms = [
            "policy",
            "source",
            "cite",
        ]

        passed = all(
            term in prompt_lower
            for term in required_terms
        )

        if not passed:
            return PromptEvaluationResult(
                case_name=case.name,
                passed=False,
                failure=(
                    "Prompt does not contain "
                    "the policy-source citation instruction."
                ),
            )

    elif case.expected_behavior == "use_retrieved_context":

        required_instruction = (
            "use retrieved context when provided"
        )

        passed = (
            required_instruction in prompt_lower
        )

        if not passed:
            return PromptEvaluationResult(
                case_name=case.name,
                passed=False,
                failure=(
                    "Prompt does not explicitly instruct "
                    "the agent to use retrieved context."
                ),
            )

    else:
        return PromptEvaluationResult(
            case_name=case.name,
            passed=False,
            failure=(
                f"Unknown expected behavior: "
                f"{case.expected_behavior}"
            ),
        )

    return PromptEvaluationResult(
        case_name=case.name,
        passed=True,
    )