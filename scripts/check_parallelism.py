"""Run the bootstrap-critical MGSM parallelism check."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.mgsm import verify_parallelism


def main() -> None:
    result = verify_parallelism(("de", "th", "sw"))
    print(result)
    if result["parallel"]:
        print("PASS: MGSM gold sequences are parallel across de/th/sw.")
        return
    print("FAIL: MGSM gold sequences are not parallel across de/th/sw.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
