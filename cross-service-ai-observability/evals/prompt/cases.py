from dataclasses import dataclass


@dataclass(frozen=True)
class PromptCase:
    name: str
    user_message: str
    expected_behavior: str


PROMPT_CASES = [

    PromptCase(
        name="policy_answer_cites_sources",
        user_message="What is our policy for handling retrieved information?",
        expected_behavior="cite_policy_sources",
    ),

    PromptCase(
        name="technical_answer_uses_context",
        user_message="Explain our RAG architecture.",
        expected_behavior="use_retrieved_context",
    ),

]
