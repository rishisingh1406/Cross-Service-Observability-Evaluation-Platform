
import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    """Load and validate a JSON file."""

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except FileNotFoundError:
        print(f"ERROR: File not found: {path}")
        raise SystemExit(2)

    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON in {path}: {exc}")
        raise SystemExit(2)


def normalize_baseline(data: dict) -> dict:
    """
    Normalize the Day 78 baseline format.

    Baseline:

        {
            "baseline": {
                "overall": {...}
            }
        }

    Current results:

        {
            "overall": {...}
        }
    """

    if "baseline" in data:
        return data["baseline"]

    return data


def get_metric(data: dict, path: str):
    """
    Retrieve a metric using a dot-separated path.

    Examples:

        overall.score
        suites.agent.score
    """

    value = data

    for key in path.split("."):

        if not isinstance(value, dict):
            return None

        if key not in value:
            return None

        value = value[key]

    return value


def check_metric(
    metric_name: str,
    baseline_value: float,
    current_value: float,
    allowed_regression: float,
) -> bool:
    """
    Check whether a metric regressed beyond its threshold.
    """

    regression = (
        baseline_value - current_value
    )

    passed = (
        regression <= allowed_regression
    )

    status = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"{status} | "
        f"{metric_name} | "
        f"baseline={baseline_value:.4f} | "
        f"current={current_value:.4f} | "
        f"regression={regression:.4f} | "
        f"allowed={allowed_regression:.4f}"
    )

    return passed


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Check evaluation results "
            "for regressions."
        )
    )

    parser.add_argument(
        "--baseline",
        required=True,
        help="Path to baseline evaluation JSON.",
    )

    parser.add_argument(
        "--current",
        required=True,
        help="Path to current evaluation JSON.",
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to regression threshold configuration.",
    )

    args = parser.parse_args()

    baseline_path = Path(
        args.baseline
    )

    current_path = Path(
        args.current
    )

    config_path = Path(
        args.config
    )

    baseline_data = load_json(
        baseline_path
    )

    current_data = load_json(
        current_path
    )

    config_data = load_json(
        config_path
    )

    baseline_data = normalize_baseline(
        baseline_data
    )

    metrics = config_data.get(
        "metrics",
        {}
    )

    if not metrics:

        print(
            "ERROR: No metrics configured."
        )

        return 2

    print("=" * 70)
    print("REGRESSION CHECK")
    print("=" * 70)

    all_passed = True

    for metric_path, metric_config in metrics.items():

        if not isinstance(
            metric_config,
            dict,
        ):

            print(
                f"FAIL | {metric_path} | "
                "invalid metric configuration"
            )

            all_passed = False

            continue

        if "max_regression" not in metric_config:

            print(
                f"FAIL | {metric_path} | "
                "missing max_regression"
            )

            all_passed = False

            continue

        allowed_regression = metric_config[
            "max_regression"
        ]

        if not isinstance(
            allowed_regression,
            (int, float),
        ):

            print(
                f"FAIL | {metric_path} | "
                "max_regression must be numeric"
            )

            all_passed = False

            continue

        baseline_value = get_metric(
            baseline_data,
            metric_path,
        )

        current_value = get_metric(
            current_data,
            metric_path,
        )

        if baseline_value is None:

            print(
                f"FAIL | {metric_path} | "
                "baseline value is unavailable"
            )

            all_passed = False

            continue

        if current_value is None:

            print(
                f"FAIL | {metric_path} | "
                "current value is unavailable"
            )

            all_passed = False

            continue

        if not isinstance(
            baseline_value,
            (int, float),
        ):

            print(
                f"FAIL | {metric_path} | "
                "baseline value is not numeric: "
                f"{baseline_value}"
            )

            all_passed = False

            continue

        if not isinstance(
            current_value,
            (int, float),
        ):

            print(
                f"FAIL | {metric_path} | "
                "current value is not numeric: "
                f"{current_value}"
            )

            all_passed = False

            continue

        passed = check_metric(
            metric_name=metric_path,
            baseline_value=float(
                baseline_value
            ),
            current_value=float(
                current_value
            ),
            allowed_regression=float(
                allowed_regression
            ),
        )

        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:

        print(
            "REGRESSION CHECK PASSED"
        )

        print("=" * 70)

        return 0

    print(
        "REGRESSION CHECK FAILED"
    )

    print("=" * 70)

    return 1


if __name__ == "__main__":
    sys.exit(main())

