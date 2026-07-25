"""Appendix-only association of translation quality with tight-budget gains."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.generate import LedgerVerificationError, read_ledger
from src.mgsm import MgsmItem, load_mgsm
from src.translation_quality import (
    ScorerProtocol,
    TranslationTriple,
    extract_translation,
)


ANALYSIS_LABEL = "EXPLORATORY - non-confirmatory (section 11; appendix only)"
ACCURACY_POLICY = (
    "Translation quality is analyzed only after accuracy scoring and never "
    "conditions, gates, excludes, reweights, or otherwise alters any accuracy result."
)


@dataclass(frozen=True)
class PeakOutcome:
    """One sample-0 item's correctness and budget-frame contribution."""

    translate_correct: int
    native_correct: int
    token_frame_gap_contribution: float


def load_sample_zero_translation_triples(
    model_keys: Sequence[str],
    ledger_root: str | Path,
    *,
    languages: Sequence[str] = ("de", "th", "sw"),
    item_loader: Callable[[str], Sequence[MgsmItem]] = load_mgsm,
) -> tuple[
    dict[tuple[str, str], list[TranslationTriple]],
    dict[tuple[str, str], int],
]:
    """Load extracted sample-0 translations aligned to English references."""
    references = list(item_loader("en"))
    if not references:
        raise ValueError("canonical English MGSM reference set is empty")
    triples_by_cell: dict[tuple[str, str], list[TranslationTriple]] = {}
    missing_by_cell: dict[tuple[str, str], int] = {}
    for model_key in model_keys:
        for language in languages:
            sources = list(item_loader(language))
            if len(sources) != len(references):
                raise ValueError(f"MGSM {language}/en item counts differ")
            aligned = []
            for source, reference in zip(sources, references):
                if (
                    source.item_id != reference.item_id
                    or source.gold != reference.gold
                ):
                    raise ValueError(
                        f"MGSM {language}/en mismatch at item {source.item_id}"
                    )
                aligned.append((source, reference))

            shard_path = (
                Path(ledger_root)
                / model_key
                / language
                / "translate_act"
                / "shard.jsonl"
            )
            selected: dict[str, Mapping[str, Any]] = {}
            for record in read_ledger(shard_path):
                if (
                    record["model_id"] != model_key
                    or record["language"] != language
                    or record["arm"] != "translate_act"
                ):
                    raise LedgerVerificationError(
                        f"{shard_path} contains a record inconsistent with its shard"
                    )
                if int(record["sample_index"]) != 0:
                    continue
                item_id = str(record["item_id"])
                if item_id in selected:
                    raise LedgerVerificationError(
                        f"{shard_path} contains duplicate sample-0 item {item_id}"
                    )
                selected[item_id] = record
            expected_ids = {source.item_id for source, _ in aligned}
            if set(selected) != expected_ids:
                raise LedgerVerificationError(
                    f"{shard_path} sample-0 items differ from MGSM"
                )

            triples = []
            missing = 0
            for source, reference in aligned:
                segment = extract_translation(
                    str(selected[source.item_id]["text"])
                )
                if segment.missing_delimiter:
                    missing += 1
                    continue
                if segment.text is None:
                    raise AssertionError("extracted translation is unexpectedly absent")
                triples.append(
                    TranslationTriple(
                        item_id=source.item_id,
                        source=source.question,
                        mt=segment.text,
                        reference=reference.question,
                    )
                )
            cell = (model_key, language)
            triples_by_cell[cell] = triples
            missing_by_cell[cell] = missing
    return triples_by_cell, missing_by_cell


def peak_outcomes_from_frames(
    frames: Mapping[str, NDArray[np.float64]],
    *,
    languages: Sequence[str],
    arms: Sequence[str],
    budgets: Sequence[int],
    peak_budgets: Mapping[str, int],
    sample_index: int = 0,
) -> dict[str, dict[str, PeakOutcome]]:
    """Extract sample-level peak outcomes from existing prefix-score frames."""
    if not {"token", "flores"} <= set(frames):
        raise ValueError("token and FLORES frames are required")
    try:
        native_index = tuple(arms).index("native")
        translate_index = tuple(arms).index("translate_act")
    except ValueError as error:
        raise ValueError("native and translate_act arms are required") from error
    if set(peak_budgets) != set(languages):
        raise ValueError("peak budgets must match the selected languages")

    token = np.asarray(frames["token"], dtype=np.float64)
    flores = np.asarray(frames["flores"], dtype=np.float64)
    if token.shape != flores.shape or token.ndim != 5:
        raise ValueError("token and FLORES frames must have the same 5-D shape")
    if not 0 <= sample_index < token.shape[4]:
        raise ValueError("sample index is outside the score frames")

    budget_indices = {int(budget): index for index, budget in enumerate(budgets)}
    results: dict[str, dict[str, PeakOutcome]] = {}
    for language_index, language in enumerate(languages):
        try:
            budget_index = budget_indices[int(peak_budgets[language])]
        except KeyError as error:
            raise ValueError(f"peak budget is not scored for {language}") from error
        native_token = token[
            :, language_index, native_index, budget_index, sample_index
        ]
        translate_token = token[
            :, language_index, translate_index, budget_index, sample_index
        ]
        native_flores = flores[
            :, language_index, native_index, budget_index, sample_index
        ]
        translate_flores = flores[
            :, language_index, translate_index, budget_index, sample_index
        ]
        selected = np.stack(
            (native_token, translate_token, native_flores, translate_flores)
        )
        if not np.isin(selected, (0.0, 1.0)).all():
            raise ValueError(f"{language} peak outcomes must be finite and binary")
        contribution = (translate_token - native_token) - (
            translate_flores - native_flores
        )
        results[language] = {
            str(item_index): PeakOutcome(
                translate_correct=int(translate_token[item_index]),
                native_correct=int(native_token[item_index]),
                token_frame_gap_contribution=float(contribution[item_index]),
            )
            for item_index in range(token.shape[0])
        }
    return results


def _rank(values: NDArray[np.float64]) -> NDArray[np.float64]:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=np.float64)
    sorted_values = values[order]
    start = 0
    while start < len(values):
        stop = start + 1
        while stop < len(values) and sorted_values[stop] == sorted_values[start]:
            stop += 1
        ranks[order[start:stop]] = (start + stop - 1) / 2.0
        start = stop
    return ranks


def _correlation(
    left: NDArray[np.float64], right: NDArray[np.float64]
) -> float | None:
    if len(left) < 2:
        return None
    left_centered = left - left.mean()
    right_centered = right - right.mean()
    denominator = float(
        np.sqrt(np.dot(left_centered, left_centered) * np.dot(right_centered, right_centered))
    )
    if denominator == 0.0:
        return None
    return float(np.dot(left_centered, right_centered) / denominator)


def _spearman(
    left: NDArray[np.float64], right: NDArray[np.float64]
) -> float | None:
    return _correlation(_rank(left), _rank(right))


def _finite_ci(values: Sequence[float | None]) -> tuple[list[float] | None, int]:
    finite = np.asarray(
        [value for value in values if value is not None and np.isfinite(value)],
        dtype=np.float64,
    )
    if not finite.size:
        return None, 0
    low, high = np.quantile(finite, [0.025, 0.975])
    return [float(low), float(high)], int(finite.size)


def _association(
    estimate: float | None, replicates: Sequence[float | None]
) -> dict[str, Any]:
    ci, valid = _finite_ci(replicates)
    return {
        "estimate": estimate,
        "bootstrap_ci_95": ci,
        "valid_bootstrap_resamples": valid,
    }


def _cell_summary(
    comet: NDArray[np.float64],
    outcomes: Sequence[PeakOutcome],
    *,
    n_boot: int,
    seed: int,
) -> dict[str, Any]:
    if n_boot < 1:
        raise ValueError("n_boot must be positive")
    if len(comet) != len(outcomes) or not len(comet):
        raise ValueError("COMET scores and outcomes must be non-empty and aligned")
    if not np.isfinite(comet).all():
        raise ValueError("COMET scores must be finite")

    translate = np.asarray(
        [outcome.translate_correct for outcome in outcomes], dtype=np.float64
    )
    native = np.asarray(
        [outcome.native_correct for outcome in outcomes], dtype=np.float64
    )
    if not np.isin(translate, (0.0, 1.0)).all() or not np.isin(
        native, (0.0, 1.0)
    ).all():
        raise ValueError("correctness outcomes must be binary")
    gain = translate - native
    win = ((translate == 1.0) & (native == 0.0)).astype(np.float64)
    contribution = np.asarray(
        [outcome.token_frame_gap_contribution for outcome in outcomes],
        dtype=np.float64,
    )
    if not np.isfinite(contribution).all():
        raise ValueError("token-frame contributions must be finite")

    rng = np.random.default_rng(seed)
    bootstrap = {
        "gain": [],
        "win": [],
        "contribution": [],
        "contrast": [],
        "contribution_mean": [],
    }
    for _ in range(n_boot):
        indices = rng.integers(0, len(comet), size=len(comet))
        sampled_comet = comet[indices]
        sampled_gain = gain[indices]
        sampled_win = win[indices]
        sampled_contribution = contribution[indices]
        bootstrap["gain"].append(_spearman(sampled_comet, sampled_gain))
        bootstrap["win"].append(_correlation(sampled_comet, sampled_win))
        bootstrap["contribution"].append(
            _spearman(sampled_comet, sampled_contribution)
        )
        if sampled_win.any() and (sampled_win == 0.0).any():
            bootstrap["contrast"].append(
                float(
                    sampled_comet[sampled_win == 1.0].mean()
                    - sampled_comet[sampled_win == 0.0].mean()
                )
            )
        else:
            bootstrap["contrast"].append(None)
        bootstrap["contribution_mean"].append(float(sampled_contribution.mean()))

    win_mask = win == 1.0
    win_mean = float(comet[win_mask].mean()) if win_mask.any() else None
    nonwin_mean = float(comet[~win_mask].mean()) if (~win_mask).any() else None
    contrast = (
        None
        if win_mean is None or nonwin_mean is None
        else float(win_mean - nonwin_mean)
    )
    contrast_ci, contrast_valid = _finite_ci(bootstrap["contrast"])
    contribution_ci, contribution_valid = _finite_ci(
        bootstrap["contribution_mean"]
    )
    counts = Counter(int(value) for value in gain)
    return {
        "n_items": len(comet),
        "correctness_gain_counts": {
            str(value): counts.get(value, 0) for value in (-1, 0, 1)
        },
        "translate_win_n": int(win.sum()),
        "spearman_comet_vs_correctness_gain": _association(
            _spearman(comet, gain), bootstrap["gain"]
        ),
        "point_biserial_comet_vs_translate_win": _association(
            _correlation(comet, win), bootstrap["win"]
        ),
        "mean_comet": {
            "translate_win": win_mean,
            "not_translate_win": nonwin_mean,
            "difference_win_minus_not": contrast,
            "difference_bootstrap_ci_95": contrast_ci,
            "valid_bootstrap_resamples": contrast_valid,
        },
        "token_frame_gap_contribution": {
            "mean": float(contribution.mean()),
            "mean_bootstrap_ci_95": contribution_ci,
            "valid_mean_bootstrap_resamples": contribution_valid,
            "spearman_comet_vs_contribution": _association(
                _spearman(comet, contribution), bootstrap["contribution"]
            ),
        },
    }


def _verdict(models: Mapping[str, Mapping[str, Mapping[str, Any]]]) -> str:
    cells = [
        cell
        for languages in models.values()
        for cell in languages.values()
    ]
    rhos = [
        float(cell["spearman_comet_vs_correctness_gain"]["estimate"])
        for cell in cells
        if cell["spearman_comet_vs_correctness_gain"]["estimate"] is not None
    ]
    point_biserials = [
        float(cell["point_biserial_comet_vs_translate_win"]["estimate"])
        for cell in cells
        if cell["point_biserial_comet_vs_translate_win"]["estimate"] is not None
    ]
    contrasts = [
        float(cell["mean_comet"]["difference_win_minus_not"])
        for cell in cells
        if cell["mean_comet"]["difference_win_minus_not"] is not None
    ]
    if not rhos:
        return (
            "At the prespecified tight/peak budgets, the correctness-gain "
            "association was undefined because no cell had outcome variation. "
            "The translate-win association was likewise not estimable. "
            "No quality/gain direction can be inferred from these cells. "
            "Overall, the analysis provides no evidence that translation quality "
            "explains the budget-sensitive advantage."
        )
    positive_excludes_zero = sum(
        ci is not None and ci[0] > 0.0
        for cell in cells
        if (
            ci := cell["spearman_comet_vs_correctness_gain"][
                "bootstrap_ci_95"
            ]
        )
        is not None
    )
    negative_excludes_zero = sum(
        ci is not None and ci[1] < 0.0
        for cell in cells
        if (
            ci := cell["spearman_comet_vs_correctness_gain"][
                "bootstrap_ci_95"
            ]
        )
        is not None
    )
    positive = sum(rho > 0.0 for rho in rhos)
    moderate = sum(abs(rho) >= 0.20 for rho in rhos)
    point_range = (
        "not estimable"
        if not point_biserials
        else f"{min(point_biserials):.3f} to {max(point_biserials):.3f}"
    )
    contrast_range = (
        "not estimable"
        if not contrasts
        else f"{min(contrasts):.3f} to {max(contrasts):.3f}"
    )
    consistent = (
        positive >= int(np.ceil(2 * len(rhos) / 3))
        and moderate >= int(np.ceil(2 * len(rhos) / 3))
        and positive_excludes_zero >= int(np.ceil(2 * len(rhos) / 3))
        and negative_excludes_zero == 0
    )
    conclusion = (
        "Overall, the cells show consistent evidence that TRANSLATE-ACT's "
        "tight-budget advantage is larger when its translation quality is higher."
        if consistent
        else "Overall, the cells do not show a consistent strong relationship, "
        "so the budget-sensitive advantage is not well explained as a translation-"
        "quality confound."
    )
    return (
        "At the prespecified tight/peak budgets, Spearman COMET-versus-"
        f"correctness-gain correlations ranged from {min(rhos):.3f} to "
        f"{max(rhos):.3f} across {len(rhos)} model-language cells. "
        f"{positive} of {len(rhos)} correlations were positive, and {moderate} "
        f"of {len(rhos)} met the moderate-magnitude threshold "
        "(absolute rho >= 0.20); "
        f"{positive_excludes_zero} positive and {negative_excludes_zero} negative "
        "bootstrap intervals excluded zero. "
        f"Mean COMET win-minus-non-win contrasts ranged from {contrast_range}; "
        f"point-biserial associations ranged from {point_range}. "
        f"{conclusion}"
    )


def analyze_comet_gain_associations(
    triples_by_cell: Mapping[tuple[str, str], Sequence[TranslationTriple]],
    outcomes_by_cell: Mapping[tuple[str, str], Mapping[str, PeakOutcome]],
    peak_budgets: Mapping[tuple[str, str], int],
    scorer: ScorerProtocol,
    *,
    n_boot: int = 10_000,
    seed: int = 20_260_725,
) -> dict[str, Any]:
    """Score translations and summarize item-level quality/gain associations."""
    cells = list(triples_by_cell)
    if set(cells) != set(outcomes_by_cell) or set(cells) != set(peak_budgets):
        raise ValueError("translation, outcome, and peak-budget cells must match")
    all_triples = [
        triple for cell in cells for triple in triples_by_cell[cell]
    ]
    raw_scores = scorer.score_batch(all_triples)
    if set(raw_scores) != {"COMET"}:
        raise ValueError("correlation analysis requires exactly one COMET score vector")
    scores = np.asarray(raw_scores["COMET"], dtype=np.float64)
    if len(scores) != len(all_triples):
        raise ValueError("COMET returned the wrong number of item scores")

    models: dict[str, dict[str, Any]] = {}
    offset = 0
    for cell_index, (model_key, language) in enumerate(cells):
        triples = list(triples_by_cell[(model_key, language)])
        item_ids = [triple.item_id for triple in triples]
        if len(set(item_ids)) != len(item_ids):
            raise ValueError(f"duplicate translation item in {model_key}/{language}")
        outcomes = outcomes_by_cell[(model_key, language)]
        try:
            aligned_outcomes = [outcomes[item_id] for item_id in item_ids]
        except KeyError as error:
            raise ValueError(
                f"missing outcome for {model_key}/{language} item {error.args[0]}"
            ) from error
        end = offset + len(triples)
        summary = _cell_summary(
            scores[offset:end],
            aligned_outcomes,
            n_boot=n_boot,
            seed=seed + cell_index,
        )
        summary["sample_index"] = 0
        summary["peak_budget_tokens"] = int(peak_budgets[(model_key, language)])
        models.setdefault(model_key, {})[language] = summary
        offset = end

    report = {
        "analysis_label": ANALYSIS_LABEL,
        "scope": "Appendix-only per-item COMET association at prespecified peak budgets",
        "accuracy_policy": ACCURACY_POLICY,
        "scorer": {
            "name": scorer.name,
            "type": scorer.scorer_type,
            "metric": "COMET",
        },
        "bootstrap": {
            "method": "item percentile bootstrap",
            "confidence_level": 0.95,
            "n_resamples": n_boot,
            "seed": seed,
        },
        "binary_association": (
            "Point-biserial correlation between COMET and the indicator that "
            "TRANSLATE-ACT is correct while NATIVE is wrong."
        ),
        "models": models,
    }
    report["verdict"] = _verdict(models)
    return report


def _format_estimate(value: float | None) -> str:
    return "NA" if value is None else f"{value:.3f}"


def _format_ci(value: Sequence[float] | None) -> str:
    return "NA" if value is None else f"[{value[0]:.3f}, {value[1]:.3f}]"


def comet_gain_markdown(report: Mapping[str, Any]) -> str:
    """Render the appendix-only COMET/gain association report."""
    lines = [
        "# COMET and tight-budget TRANSLATE-ACT gains",
        "",
        "**Exploratory, non-confirmatory, appendix only.** Translation quality "
        "never conditions, gates, excludes, reweights, or otherwise alters an "
        "accuracy result.",
        "",
        "Correctness gain is `I[TRANSLATE-ACT correct] - I[NATIVE correct]` at "
        "the prespecified peak token budget using `sample_index = 0`. A translate "
        "win is the binary event that TRANSLATE-ACT is correct and NATIVE is "
        "wrong. The token-frame gap contribution is the per-item token-frame "
        "gain minus its FLORES-frame counterpart.",
        "",
        "| Model | Language | Peak budget | n | TA wins | Spearman rho | 95% CI "
        "| Point-biserial r | 95% CI | COMET win | COMET non-win | Difference "
        "| Difference 95% CI | Token-frame contribution | Contribution 95% CI "
        "| COMET/contribution rho | 95% CI |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: "
        "| ---: | ---: | --- | ---: | --- | ---: | --- |",
    ]
    for model_key, languages in report["models"].items():
        for language, cell in languages.items():
            spearman = cell["spearman_comet_vs_correctness_gain"]
            point_biserial = cell[
                "point_biserial_comet_vs_translate_win"
            ]
            means = cell["mean_comet"]
            contribution = cell["token_frame_gap_contribution"]
            contribution_association = contribution[
                "spearman_comet_vs_contribution"
            ]
            lines.append(
                f"| {model_key} | {language} | "
                f"{cell['peak_budget_tokens']} | {cell['n_items']} | "
                f"{cell['translate_win_n']} | "
                f"{_format_estimate(spearman['estimate'])} | "
                f"{_format_ci(spearman['bootstrap_ci_95'])} | "
                f"{_format_estimate(point_biserial['estimate'])} | "
                f"{_format_ci(point_biserial['bootstrap_ci_95'])} | "
                f"{_format_estimate(means['translate_win'])} | "
                f"{_format_estimate(means['not_translate_win'])} | "
                f"{_format_estimate(means['difference_win_minus_not'])} | "
                f"{_format_ci(means['difference_bootstrap_ci_95'])} | "
                f"{_format_estimate(contribution['mean'])} | "
                f"{_format_ci(contribution['mean_bootstrap_ci_95'])} | "
                f"{_format_estimate(contribution_association['estimate'])} | "
                f"{_format_ci(contribution_association['bootstrap_ci_95'])} |"
            )
    lines.extend(
        [
            "",
            "## Reviewer verdict",
            "",
            str(report["verdict"]),
            "",
        ]
    )
    return "\n".join(lines)
