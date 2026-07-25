"""Run the Phase 3 Llama-3.1-8B-Instruct generation."""

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.engine import VLLMEngine
from src.run_full import run_model


def main() -> None:
    engine = VLLMEngine(
        "http://[::1]:9001",
        enable_thinking=True,
    )
    print(
        json.dumps(
            run_model("llama_3_1_8b_instruct", engine),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
