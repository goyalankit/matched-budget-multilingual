# BLIND regeneration drift audit

`prereg-budget-aware.md` §4.2. One shard: qwen3_8b native `de` at `B=192`, 2,000 records, E1 seeds (`base_seed` 20260726).

Tolerance declared before the run: the E1 within-cell bootstrap standard error of each statistic (10,000 item-clustered resamples on the stored shard).

| statistic | stored | regenerated | difference | tolerance (SE) | within |
|---|---:|---:|---:|---:|---|
| mean_output_tokens | 184.7665 | 184.7025 | -0.0640 | 1.0006 | yes |
| eos_rate | 0.1995 | 0.1990 | -0.0005 | 0.0203 | yes |
| accuracy | 0.1615 | 0.1595 | -0.0020 | 0.0178 | yes |

Bitwise-identical share: 58.9%. Descriptive only: E1 measures ~46% bitwise determinism on repeat, so this is not a tolerance and a low value is not drift.

**Verdict: reuse.** All three statistics are inside the declared tolerance; the stored BLIND shards are reused as §4.2 specifies.
