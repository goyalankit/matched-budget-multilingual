# Sub-CDF predictor validation (Qwen3-8B, NATIVE)

Predictor from `runs/` (long-cap). Observed peaks from the independent sweep.
**Measurement, not a fit** — nothing is tuned to improve agreement.

| Lang | Window | Observed | Sub-CDF | Err | Product form | Err |
|---|---|---:|---:|---:|---:|---:|
| de | (192, 299] | 34.65 | 33.65 | -1.00 | 29.94 | -4.71 |
| th | (256, 652] | 38.60 | 38.85 | +0.25 | 36.69 | -1.91 |
| sw | (128, 247] | 13.70 | 14.90 | +1.20 | 10.48 | -3.22 |

Mean |error|: sub-CDF 0.82 pts, product form 3.28 pts.

Llama skipped: tokenizer not cached locally.
