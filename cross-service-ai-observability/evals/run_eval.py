import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Make the project root importable so that:
# from evals.prompt...
# works when this file is executed directly.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from evals.prompt.cases import PROMPT_CASES
from evals.prompt.evaluator import evaluate_prompt_case

# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_PATH = PROJECT_ROOT / "evals" / "results.json"

REGISTRY_PATH = PROJECT_ROOT / "prompts" / "registry.json"

PROMPT_BASELINE_PATH = (
    PROJECT_ROOT
    / "evals"
    / "prompt"
    / "baseline.json"
)

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


agent_prompt_version = prompt_registry["agent"]["version"]

AGENT_PROMPT_PATH = (
    PROJECT_ROOT
    / prompt_registry["agent"]["prompt_path"]
)


with open(
    AGENT_PROMPT_PATH,
    "r",
    encoding="utf-8",
) as f:
    agent_system_prompt = f.read()


# ============================================================
# PYTEST RUNNER
# ============================================================

def run_pytest(
    test_path: str,
    junit_name: str,
):
    JUNIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    junit_path = JUNIT_DIR / junit_name

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

    failed = 0
    skipped = 0
    errors = 0
    total = 0

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

            total += int(
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

    actual_passed = (
        total
        - failed
        - errors
        - skipped
    )

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
# PROMPT EVALUATION
# ============================================================

def run_prompt_evaluation():

    passed = 0
    failed = 0
    failures = []

    for case in PROMPT_CASES:

        result = evaluate_prompt_case(
            case,
            agent_system_prompt,
        )

        if result.passed:

            passed += 1

        else:

            failed += 1

            failures.append(
                {
                    "case": result.case_name,
                    "failure": result.failure,
                }
            )

    total = len(PROMPT_CASES)

    score = (
        round(
            passed / total,
            4,
        )
        if total > 0
        else None
    )

    return {
        "passed": passed,
        "failed": failed,
        "skipped": 0,
        "errors": 0,
        "total": total,
        "score": score,
        "failures": failures,
        "exit_code": 0 if failed == 0 else 1,
    }


# ============================================================
# PROMPT REGRESSION
# ============================================================

def load_prompt_baseline():
    """
    Load the expected healthy prompt behavior score.

    utf-8-sig is used so the evaluator works with both:
    - normal UTF-8 JSON
    - UTF-8 JSON files containing a Windows BOM
    """

    if not PROMPT_BASELINE_PATH.exists():
        raise FileNotFoundError(
            f"Prompt baseline file not found: "
            f"{PROMPT_BASELINE_PATH}"
        )

    with open(
        PROMPT_BASELINE_PATH,
        "r",
        encoding="utf-8-sig",
    ) as f:
        baseline = json.load(f)

    if "prompt_behavior_score" not in baseline:
        raise ValueError(
            "Prompt baseline must contain "
            "'prompt_behavior_score'."
        )

    return float(
        baseline["prompt_behavior_score"]
    )


def evaluate_prompt_regression(
    current_score,
):
    baseline_score = load_prompt_baseline()

    if current_score is None:

        return {
            "baseline": baseline_score,
            "current": None,
            "change": None,
            "change_percent": None,
            "regression": False,
        }

    change = round(
        current_score - baseline_score,
        4,
    )

    change_percent = (
        round(
            (change / baseline_score) * 100,
            2,
        )
        if baseline_score != 0
        else 0.0
    )

    regression = (
        current_score < baseline_score
    )

    return {
        "baseline": baseline_score,
        "current": current_score,
        "change": change,
        "change_percent": change_percent,
        "regression": regression,
    }


def print_prompt_regression_table(
    regression,
):

    print()
    print("=" * 70)
    print("PROMPT REGRESSION TABLE")
    print("=" * 70)

    print(
        f"{'Metric':<28}"
        f"{'Baseline':>12}"
        f"{'Current':>12}"
        f"{'Change':>12}"
    )

    print("-" * 70)

    baseline = regression["baseline"]
    current = regression["current"]
    change_percent = regression["change_percent"]

    if current is None:

        print(
            f"{'Prompt Behavior Score':<28}"
            f"{baseline:>11.2%}"
            f"{'N/A':>12}"
            f"{'N/A':>12}"
        )

    else:

        print(
            f"{'Prompt Behavior Score':<28}"
            f"{baseline:>11.2%}"
            f"{current:>11.2%}"
            f"{change_percent:>11.2f}%"
        )

    print("-" * 70)

    if regression["regression"]:

        print()
        print(
            "❌ PROMPT REGRESSION DETECTED"
        )

        print(
            f"Baseline: "
            f"{baseline:.2%}"
        )

        print(
            f"Current:  "
            f"{current:.2%}"
        )

        print(
            f"Drop:     "
            f"{abs(change_percent):.2f}%"
        )

    else:

        print()
        print(
            "✅ NO PROMPT REGRESSION DETECTED"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "DAY 80 — PROMPT REGRESSION EVALUATION"
    )
    print("=" * 70)

    print(
        f"Prompt version: "
        f"{agent_prompt_version}"
    )

    print()

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    print(
        "Running RAG evaluation..."
    )

    rag_results = run_pytest(
        "evals/rag",
        "rag.xml",
    )

    if rag_results["total"] == 0:

        print(
            "RAG: 0 tests (not evaluated)"
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

    print(
        "Running Agent evaluation..."
    )

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
    # PROMPT
    # --------------------------------------------------------

    print()
    print(
        "Running Prompt evaluation..."
    )

    prompt_results = run_prompt_evaluation()

    print(
        f"Prompt: "
        f"{prompt_results['passed']}/"
        f"{prompt_results['total']} passed"
    )

    for failure in prompt_results["failures"]:

        print(
            f"FAIL | "
            f"{failure['case']} | "
            f"{failure['failure']}"
        )

    # --------------------------------------------------------
    # PROMPT REGRESSION CHECK
    # --------------------------------------------------------

    prompt_regression = (
        evaluate_prompt_regression(
            prompt_results["score"]
        )
    )

    print_prompt_regression_table(
        prompt_regression
    )

    # --------------------------------------------------------
    # AGGREGATE
    # --------------------------------------------------------

    suites = {
        "rag": rag_results,
        "agent": agent_results,
        "prompt": prompt_results,
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

        "suites": suites,

        "prompt_regression": (
            prompt_regression
        ),

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
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(
        f"Overall: "
        f"{total_passed}/"
        f"{total_tests}"
    )

    if overall_score is None:

        print(
            "Score: N/A — no tests collected"
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
    # FAIL EVALUATION
    # --------------------------------------------------------

    if (
        total_failed > 0
        or prompt_regression["regression"]
    ):

        print()
        print(
            "EVALUATION FAILED"
        )

        if prompt_regression["regression"]:

            print(
                "Reason: prompt behavior score "
                "regressed from "
                f"{prompt_regression['baseline']:.2%} "
                "to "
                f"{prompt_regression['current']:.2%}."
            )

        raise SystemExit(1)

    print()
    print(
        "EVALUATION PASSED"
    )


if __name__ == "__main__":
    main()