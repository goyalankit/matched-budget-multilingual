"""Run the preregistered formatting-only pilot against Qwen3-8B."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.engine import VLLMEngine
from src.pilot import run_pilot


def _print_report(report: dict[str, object]) -> None:
    print(
        f"{'Language':<10} {'Arm':<16} {'N':>3} "
        f"{'Parse fail':>12} {'Missing delimiter':>18} {'>10%':>6}"
    )
    print("-" * 71)
    for cell in report["cells"]:
        print(
            f"{cell['language']:<10} {cell['arm']:<16} {cell['n']:>3} "
            f"{cell['parse_failure_rate']:>11.1%} "
            f"{cell['missing_delimiter_rate']:>17.1%} "
            f"{'YES' if cell['over_10pct'] else 'no':>6}"
        )

    flagged = [
        f"{cell['language']}/{cell['arm']}"
        for cell in report["cells"]
        if cell["over_10pct"]
    ]
    if flagged:
        print(
            "\nGovernance HOLD (>10%): "
            + ", ".join(flagged)
            + ". A documented amendment commit is required before prompt/parser "
            "changes; verify the residual failures are formatting defects, not "
            "genuine non-integer/truncated answers (see tasks/pilot-governance-note.md)."
        )
    else:
        print("\nGovernance PASS: no cell exceeds 10%.")


def main() -> None:
    engine = VLLMEngine(
        "http://[::1]:9002",
        enable_thinking=False,
    )
    _print_report(run_pilot(engine))


if __name__ == "__main__":
    main()
