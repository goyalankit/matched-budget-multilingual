"""Run the Phase 3 Qwen3-8B generation."""

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.engine import VLLMEngine
from src.run_full import run_model


def main() -> None:
    engine = VLLMEngine(
        "http://[::1]:9002",
        enable_thinking=False,
    )
    print(json.dumps(run_model("qwen3_8b", engine), sort_keys=True))


if __name__ == "__main__":
    main()
