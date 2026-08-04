#!/usr/bin/env python3
"""Plot the measured native-vs-translate gap by output budget for both models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "figures" / "gap_curves.png"
MODELS = (
    ("explore_budget_qwen.json", "Qwen3-8B"),
    ("explore_budget_llama.json", "Llama-3.1-8B-Instruct"),
)
# Okabe-Ito-derived trio; passes CVD-separation and contrast validation.
COLORS = {"de": "#0072B2", "th": "#D55E00", "sw": "#009E73"}
MARKERS = {"de": "o", "th": "s", "sw": "^"}
LANGUAGE_NAMES = {"de": "German", "th": "Thai", "sw": "Swahili"}


def load_gaps(path: Path) -> tuple[list[int], dict[str, list[float]]]:
    data = json.loads(path.read_text(encoding="utf-8"))["small_budget"]
    budgets = [int(b) for b in data["budgets_tokens"]]
    gaps: dict[str, list[float]] = {}
    for language, arms in data["token_accuracy_points"].items():
        native = arms["native"]
        translate = arms["translate_act"]
        gaps[language] = [translate[str(b)] - native[str(b)] for b in budgets]
    return budgets, gaps


def render(output_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.4), sharey=True)

    for axis, (filename, title) in zip(axes, MODELS):
        budgets, gaps = load_gaps(ROOT / "analysis-out" / filename)
        axis.axhline(0, color="0.45", linestyle="--", linewidth=1, zorder=1)
        for language in ("de", "th", "sw"):
            axis.plot(
                budgets,
                gaps[language],
                color=COLORS[language],
                marker=MARKERS[language],
                markersize=5,
                linewidth=2,
                label=LANGUAGE_NAMES[language],
                zorder=3,
            )
            axis.annotate(
                LANGUAGE_NAMES[language],
                (budgets[-1], gaps[language][-1]),
                xytext=(6, 0),
                textcoords="offset points",
                fontsize=9,
                va="center",
                color=COLORS[language],
            )
        axis.set_xscale("log", base=2)
        axis.set_xticks((64, 128, 256, 512, 1024))
        axis.set_xticklabels(("64", "128", "256", "512", "1024"))
        axis.set_xlim(60, 1500)
        axis.set_title(title)
        axis.set_xlabel("Prefix budget")
        axis.grid(axis="y", alpha=0.25)

    axes[0].set_ylabel(r"gap$(B)$ = TRANSLATE-ACT $-$ NATIVE (points)")
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle("Measured native-vs-translate gap by output budget")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    render(args.output)


if __name__ == "__main__":
    main()
