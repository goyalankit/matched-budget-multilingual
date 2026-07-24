"""Pure prefix-budget mappings from preregistration §§4 and 5."""

from math import floor
from typing import List, Optional, Tuple

_TOKEN_CHECKPOINTS = (512, 1024, 2048, 4096)
_MAX_GENERATION_TOKENS = 4096


def token_checkpoint_prefix(output_token_count: int, B: int, eos: bool) -> int:
    """Return the stored trace length evaluated at token checkpoint ``B``."""
    if eos and output_token_count < B:
        return output_token_count
    return min(output_token_count, B)


def dollar_prefix(
    c: float, p_in: float, p_out: float, input_tokens: int, n_i: int
) -> Tuple[bool, int]:
    """Map a dollar checkpoint to a stored output prefix per prereg §5.2."""
    input_cost = p_in * input_tokens
    if input_cost > c:
        return False, 0
    affordable_tokens = floor((c - input_cost) / p_out)
    return True, min(n_i, affordable_tokens)


def flores_prefix(B: int, r: float) -> Optional[int]:
    """Map a normalized budget per prereg §5.3, without clamping."""
    prefix_length = floor(r * B)
    if prefix_length > _MAX_GENERATION_TOKENS:
        return None
    return prefix_length


def dollar_grid(p_out: float) -> List[float]:
    """Construct the deterministic output-price grid from prereg §5.2."""
    return [p_out * checkpoint for checkpoint in _TOKEN_CHECKPOINTS]
