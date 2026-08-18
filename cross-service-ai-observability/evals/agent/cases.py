from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingCase:
    name: str
    message: str

    expected_route: str

    retrieval_expected: bool
    memory_expected: bool
    llm_expected: bool


ROUTING_CASES = [

    # --------------------------------------------------
    # Retrieval cases
    # --------------------------------------------------

    RoutingCase(
        name="policy_question_uses_retrieval",
        message="What is our RAG architecture?",
        expected_route="retrieval",
        retrieval_expected=True,
        memory_expected=False,
        llm_expected=True,
    ),

    RoutingCase(
        name="distributed_system_question_uses_retrieval",
        message="How does our distributed system work?",
        expected_route="retrieval",
        retrieval_expected=True,
        memory_expected=False,
        llm_expected=True,
    ),

    RoutingCase(
        name="observability_question_uses_retrieval",
        message="How does our observability system work?",
        expected_route="retrieval",
        retrieval_expected=True,
        memory_expected=False,
        llm_expected=True,
    ),

    RoutingCase(
        name="agent_architecture_question_uses_retrieval",
        message="Explain our agent architecture.",
        expected_route="retrieval",
        retrieval_expected=True,
        memory_expected=False,
        llm_expected=True,
    ),

    # --------------------------------------------------
    # Memory cases
    # --------------------------------------------------

    RoutingCase(
        name="returning_user_uses_memory",
        message="What do you remember about me?",
        expected_route="memory",
        retrieval_expected=False,
        memory_expected=True,
        llm_expected=True,
    ),

    RoutingCase(
        name="remember_request_uses_memory",
        message="Remember that I prefer Python.",
        expected_route="memory",
        retrieval_expected=False,
        memory_expected=True,
        llm_expected=True,
    ),

    RoutingCase(
        name="previous_context_uses_memory",
        message="Based on what I told you earlier, what should I do?",
        expected_route="memory",
        retrieval_expected=False,
        memory_expected=True,
        llm_expected=True,
    ),

    # --------------------------------------------------
    # Chit-chat cases
    # --------------------------------------------------

    RoutingCase(
        name="greeting_skips_tools",
        message="Hey, how are you?",
        expected_route="direct",
        retrieval_expected=False,
        memory_expected=False,
        llm_expected=True,
    ),

    RoutingCase(
        name="casual_conversation_skips_tools",
        message="Nice to meet you!",
        expected_route="direct",
        retrieval_expected=False,
        memory_expected=False,
        llm_expected=True,
    ),

    RoutingCase(
        name="simple_thanks_skips_tools",
        message="Thanks!",
        expected_route="direct",
        retrieval_expected=False,
        memory_expected=False,
        llm_expected=True,
    ),
]
