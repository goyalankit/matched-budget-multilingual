"""Run the E1 independent-decoding generation for one model.

Protocol: `prereg-independent-decoding.md`. Requires tag `independent-protocol-freeze`.

    python scripts/run_independent.py qwen3_8b --concurrency 128
    python scripts/run_independent.py llama_3_1_8b_instruct --concurrency 128
"""

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.engine import VLLMEngine
from src.run_independent import run_model_independent

# Frozen in configs/models.yaml.
ENDPOINTS = {
    "qwen3_8b": "http://[::1]:9002",
    "llama_3_1_8b_instruct": "http://[::1]:9001",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_key", choices=sorted(ENDPOINTS))
    parser.add_argument("--concurrency", type=int, default=128)
    parser.add_argument("--out-dir", default="runs-independent")
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="write the run report JSON here (protocol §10 records concurrency)",
    )
    args = parser.parse_args()

    engine = VLLMEngine(ENDPOINTS[args.model_key], enable_thinking=False)
    report = run_model_independent(
        args.model_key,
        engine,
        concurrency=args.concurrency,
        out_dir=args.out_dir,
    )
    payload = json.dumps(report, sort_keys=True)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
