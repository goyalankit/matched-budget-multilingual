"""Check repeated-seed token-ID determinism against the live vLLM server."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.engine import VLLMEngine
from src.mgsm import load_mgsm
from src.seeds import seed

_ARMS = ("native", "translate_act", "pivot", "code_switched")
_LANGUAGES = ("de", "th", "sw")
_BASE_SEED = 20260724
_MAX_TOKENS = 512
_N_INSTANCES = 50


def main() -> None:
    engine = VLLMEngine("http://[::1]:9002")
    items_by_language = {language: load_mgsm(language) for language in _LANGUAGES}
    identical = 0

    for instance_index in range(_N_INSTANCES):
        language = _LANGUAGES[instance_index % len(_LANGUAGES)]
        arm = _ARMS[(instance_index // len(_LANGUAGES)) % len(_ARMS)]
        item = items_by_language[language][instance_index]
        sample_index = instance_index % 8
        prompt_template = (_ROOT / "prompts" / arm / f"{language}.txt").read_text(
            encoding="utf-8"
        )
        prompt = prompt_template.replace("{problem}", item.question)
        generation_seed = seed(
            base_seed=_BASE_SEED,
            item_id=item.item_id,
            sample_index=sample_index,
        )

        first = engine.generate(prompt, generation_seed, _MAX_TOKENS)
        second = engine.generate(prompt, generation_seed, _MAX_TOKENS)
        if list(first.token_ids) == list(second.token_ids):
            identical += 1

    print(
        f"Identical token IDs: {identical}/{_N_INSTANCES} "
        f"({identical / _N_INSTANCES:.1%})"
    )
    if identical < _N_INSTANCES:
        print(
            "NOTE: Engine nondeterminism observed; budget checkpoints remain "
            "prefixes of each stored generation."
        )


if __name__ == "__main__":
    main()
