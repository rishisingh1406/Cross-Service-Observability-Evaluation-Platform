import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_PATH = PROJECT_ROOT / "evals" / "results.json"
REGISTRY_PATH = PROJECT_ROOT / "prompts" / "registry.json"

JUNIT_DIR = PROJECT_ROOT / "evals" / ".junit"


# ============================================================
# LOAD PROMPT REGISTRY
# ============================================================

with open(
    REGISTRY_PATH,
    "r",
    encoding="utf-8",
) as f:
    prompt_registry = json.load(f)


agent_prompt_version = (
    prompt_registry["agent"]["version"]
)


# ============================================================
# PYTEST RUNNER
# ============================================================

def run_pytest(
    test_path: str,
    junit_name: str,
):
    """
    Run a pytest suite and return structured results.

    Pytest writes JUnit XML so that this evaluator does not
    depend on parsing human-readable terminal output.
    """

    JUNIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    junit_path = (
        JUNIT_DIR / junit_name
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            test_path,
            "-q",
            f"--junitxml={junit_path}",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    # --------------------------------------------------------
    # Parse JUnit XML
    # --------------------------------------------------------

    if junit_path.exists():

        root = ET.parse(
            junit_path
        ).getroot()

        test_suites = []

        if root.tag == "testsuite":
            test_suites = [root]

        elif root.tag == "testsuites":
            test_suites = root.findall(
                "testsuite"
            )

        for suite in test_suites:

            passed += int(
                suite.attrib.get(
                    "tests",
                    0,
                )
            )

            failed += int(
                suite.attrib.get(
                    "failures",
                    0,
                )
            )

            errors += int(
                suite.attrib.get(
                    "errors",
                    0,
                )
            )

            skipped += int(
                suite.attrib.get(
                    "skipped",
                    0,
                )
            )

        total = passed

        actual_passed = (
            total
            - failed
            - errors
            - skipped
        )

    else:

        total = 0
        actual_passed = 0

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    score = (
        round(
            actual_passed / total,
            4,
        )
        if total > 0
        else None
    )

    return {
        "passed": actual_passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
        "total": total,
        "score": score,
        "exit_code": result.returncode,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 78 — BASELINE EVALUATION")
    print("=" * 60)

    print(
        f"Prompt version: "
        f"{agent_prompt_version}"
    )

    print()

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    print("Running RAG evaluation...")

    rag_results = run_pytest(
        "evals/rag",
        "rag.xml",
    )

    if rag_results["total"] == 0:

        print(
            "RAG: 0 tests "
            "(not evaluated)"
        )

    else:

        print(
            f"RAG: "
            f"{rag_results['passed']}/"
            f"{rag_results['total']} passed"
        )

    # --------------------------------------------------------
    # AGENT
    # --------------------------------------------------------

    print("Running Agent evaluation...")

    agent_results = run_pytest(
        "evals/agent",
        "agent.xml",
    )

    print(
        f"Agent: "
        f"{agent_results['passed']}/"
        f"{agent_results['total']} passed"
    )

    # --------------------------------------------------------
    # AGGREGATE
    # --------------------------------------------------------

    suites = {
        "rag": rag_results,
        "agent": agent_results,
    }

    total_passed = sum(
        suite["passed"]
        for suite in suites.values()
    )

    total_failed = sum(
        suite["failed"]
        + suite["errors"]
        for suite in suites.values()
    )

    total_tests = sum(
        suite["total"]
        for suite in suites.values()
    )

    overall_score = (
        round(
            total_passed / total_tests,
            4,
        )
        if total_tests > 0
        else None
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    results = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "prompt_version": (
            agent_prompt_version
        ),

        "model": "mock-v1",

        "suites": {
            "rag": rag_results,
            "agent": agent_results,
        },

        "overall": {
            "passed": total_passed,
            "failed": total_failed,
            "total": total_tests,
            "score": overall_score,
        },
    }

    # --------------------------------------------------------
    # WRITE RESULTS
    # --------------------------------------------------------

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
        )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(
        f"Overall: "
        f"{total_passed}/"
        f"{total_tests}"
    )

    if overall_score is None:

        print(
            "Score: "
            "N/A — no tests collected"
        )

    else:

        print(
            f"Score: "
            f"{overall_score:.2%}"
        )

    print(
        f"Prompt version: "
        f"{agent_prompt_version}"
    )

    print(
        "Model: mock-v1"
    )

    print()
    print(
        f"Saved: "
        f"{RESULTS_PATH}"
    )

    # --------------------------------------------------------
    # Fail the evaluator if any actual tests failed
    # --------------------------------------------------------

    if total_failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()