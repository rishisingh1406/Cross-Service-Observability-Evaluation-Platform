from pathlib import Path


PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / "agent"
    / "system.txt"
)

REQUIRED_RETRIEVAL_INSTRUCTION = (
    "Use retrieved context when provided."
)


def test_retrieval_instruction_is_present():
    """
    Permanent regression guard for Day 82.

    The production agent must explicitly instruct the model
    to use retrieved context when retrieval provides it.

    If this instruction is removed from system.txt, this test
    must fail.
    """

    prompt = PROMPT_PATH.read_text(encoding="utf-8")

    assert REQUIRED_RETRIEVAL_INSTRUCTION in prompt, (
        "Retrieval prompt regression detected: "
        "the production system prompt is missing the required "
        "retrieval instruction."
    )
