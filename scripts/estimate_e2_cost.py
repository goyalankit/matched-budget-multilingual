"""Compute the E2 cost estimate from the stored ledgers (`prereg-budget-aware.md` §6).

Reads only. Writes the estimate to `analysis-out/`; nothing under any `runs-*`
directory is touched.

    python scripts/estimate_e2_cost.py \
        --json-out analysis-out/e2_cost.json \
        --markdown-out analysis-out/e2_cost.md
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.e2_cost import main

if __name__ == "__main__":
    main()
