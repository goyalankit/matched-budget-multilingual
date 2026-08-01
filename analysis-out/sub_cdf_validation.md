# Sub-CDF predictor validation (Qwen3-8B, NATIVE)

Predictor from `runs/` (long-cap). Observed peaks from the independent sweep.
**Measurement, not a fit** — nothing is tuned to improve agreement.

| Lang | Window | Observed | Sub-CDF | Err | Product form | Err |
|---|---|---:|---:|---:|---:|---:|
| de | (192, 299] | 34.65 | 34.20 | -0.45 | 30.41 | -4.23 |
| th | (256, 652] | 38.60 | 38.85 | +0.25 | 36.69 | -1.91 |
| sw | (128, 247] | 13.70 | 14.95 | +1.25 | 10.53 | -3.17 |

Mean |error|: sub-CDF 0.65 pts, product form 3.10 pts.

Llama skipped: tokenizer not cached locally.
