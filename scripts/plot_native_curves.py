#!/usr/bin/env python3
"""Plot Qwen NATIVE accuracy curves and peak premium windows from the ledger."""

from __future__ import annotations

import argparse
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "analysis-out" / "explore_budget_qwen.md"
DEFAULT_OUTPUT = ROOT / "figures" / "native_curves.png"
PEAKS = {
    "de": (192, 1.558886, 50.30, 34.2),
    "th": (256, 2.550777, 45.05, 38.9),
    "sw": (128, 1.936317, 23.65, 15.0),
}
LANGUAGE_NAMES = {"de": "German", "th": "Thai", "sw": "Swahili"}


def parse_native_curves(path: Path) -> tuple[list[int], dict[str, list[float]]]:
    in_accuracy_table = False
    budgets: list[int] = []
    curves: dict[str, list[float]] = {}

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "## Token-frame accuracy curves":
            in_accuracy_table = True
            continue
        if not in_accuracy_table or not line.startswith("|"):
            continue

        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells[:2] == ["Language", "Arm"]:
            budgets = [int(value) for value in cells[2:]]
            continue
        if len(cells) >= 3 and cells[1] == "native":
            curves[cells[0]] = [float(value) for value in cells[2:]]

    if not budgets or set(curves) != set(PEAKS):
        raise ValueError(f"Could not parse Qwen native accuracy table from {path}")
    if any(len(values) != len(budgets) for values in curves.values()):
        raise ValueError(f"Budget and accuracy columns do not align in {path}")
    return budgets, curves


def render(input_path: Path, output_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    budgets, curves = parse_native_curves(input_path)
    colors = {"de": "#0072B2", "th": "#D55E00", "sw": "#009E73"}
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.4), sharey=True)

    for axis, language in zip(axes, ("de", "th", "sw")):
        peak_budget, ratio, premium_accuracy, reported_delta = PEAKS[language]
        premium_cap = math.floor(ratio * peak_budget)
        peak_accuracy = curves[language][budgets.index(peak_budget)]
        axis.plot(
            budgets,
            curves[language],
            color=colors[language],
            marker="o",
            linewidth=2,
        )
        axis.axvspan(
            peak_budget,
            premium_cap,
            color=colors[language],
            alpha=0.18,
            label=rf"$({peak_budget}, {premium_cap}]$",
        )
        axis.axvline(peak_budget, color=colors[language], linestyle="--", linewidth=1)
        axis.axvline(premium_cap, color=colors[language], linestyle=":", linewidth=1)
        axis.plot(
            [peak_budget, premium_cap, premium_cap],
            [peak_accuracy, peak_accuracy, premium_accuracy],
            color=colors[language],
            linestyle="-.",
            linewidth=1.5,
            zorder=3,
        )
        axis.scatter(
            [peak_budget, premium_cap],
            [peak_accuracy, premium_accuracy],
            color=colors[language],
            edgecolor="white",
            marker="D",
            s=55,
            linewidth=0.8,
            zorder=4,
        )
        axis.annotate(
            rf"$\Delta={reported_delta:.1f}$",
            (premium_cap, (peak_accuracy + premium_accuracy) / 2),
            xytext=(5, 0),
            textcoords="offset points",
            fontsize=9,
            va="center",
            color=colors[language],
        )
        axis.set_xscale("log", base=2)
        axis.set_xticks((64, 128, 256, 512, 1024))
        axis.set_xticklabels(("64", "128", "256", "512", "1024"))
        axis.set_xlim(60, 1100)
        axis.set_ylim(0, 85)
        axis.set_title(LANGUAGE_NAMES[language])
        axis.set_xlabel("Prefix budget")
        axis.grid(axis="y", alpha=0.25)
        axis.legend(frameon=False, loc="upper left")

    axes[0].set_ylabel("NATIVE exact-match accuracy (%)")
    fig.suptitle("Qwen3-8B native accuracy and peak premium windows")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    render(args.input, args.output)


if __name__ == "__main__":
    main()
