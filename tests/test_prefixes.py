from src.prefixes import (
    dollar_grid,
    dollar_prefix,
    flores_prefix,
    token_checkpoint_prefix,
)


def test_token_checkpoint_caps_at_eos_completed_trace() -> None:
    assert token_checkpoint_prefix(300, 512, eos=True) == 300


def test_token_checkpoint_uses_budget_for_longer_trace() -> None:
    assert token_checkpoint_prefix(4096, 512, eos=False) == 512


def test_token_checkpoint_allows_zero_token_prefix() -> None:
    assert token_checkpoint_prefix(0, 512, eos=True) == 0


def test_dollar_prefix_uses_affordable_output_tokens() -> None:
    assert dollar_prefix(10.0, 0.1, 0.2, input_tokens=20, n_i=100) == (True, 40)


def test_dollar_prefix_is_capped_at_stored_trace_length() -> None:
    assert dollar_prefix(100.0, 0.1, 0.2, input_tokens=20, n_i=30) == (True, 30)


def test_dollar_prefix_reports_input_cost_infeasibility() -> None:
    assert dollar_prefix(1.0, 0.2, 0.1, input_tokens=6, n_i=100) == (False, 0)


def test_dollar_prefix_can_feasibly_buy_zero_output_tokens() -> None:
    assert dollar_prefix(1.0, 0.2, 0.1, input_tokens=5, n_i=100) == (True, 0)


def test_flores_prefix_floors_scaled_budget() -> None:
    assert flores_prefix(1024, 1.5) == 1536


def test_flores_prefix_is_unavailable_above_generation_limit() -> None:
    assert flores_prefix(2048, 2.1) is None


def test_flores_prefix_includes_exact_generation_limit_boundary() -> None:
    assert flores_prefix(2048, 2.0) == 4096


def test_dollar_grid_uses_registered_token_checkpoints() -> None:
    assert dollar_grid(0.5) == [256.0, 512.0, 1024.0, 2048.0]
