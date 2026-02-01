from __future__ import annotations

import pytest

from src.costs import (
    CostBreakdown,
    TokenBreakdown,
    compute_cost_breakdown,
    format_cost,
    format_cost_line,
)


def test_format_cost_over_one_dollar() -> None:
    assert format_cost(1.234) == "$1.23"


def test_format_cost_under_one_dollar() -> None:
    assert format_cost(0.051) == "5.1¢"


def test_format_cost_rounds_to_zero() -> None:
    assert format_cost(0.0005) == "rounds to 0¢"


def test_format_cost_line_omits_breakdown_when_total_rounds_to_zero() -> None:
    breakdown = CostBreakdown(
        input_cost=0.0002,
        reasoning_cost=0.0002,
        output_cost=0.0001,
        total_cost=0.0005,
    )
    assert format_cost_line(breakdown) == "Cost: rounds to 0¢"


def test_format_cost_line_combines_reasoning_output() -> None:
    breakdown = CostBreakdown(
        input_cost=0.004,
        reasoning_cost=0.0,
        output_cost=0.0151,
        total_cost=0.0191,
    )
    assert (
        format_cost_line(breakdown, include_reasoning=False, output_label="reasoning+output")
        == "Cost: 1.9¢ (0.4¢ input, 1.5¢ reasoning+output)"
    )


def test_format_cost_line_omits_reasoning() -> None:
    breakdown = CostBreakdown(
        input_cost=0.004,
        reasoning_cost=0.002,
        output_cost=0.0151,
        total_cost=0.0191,
    )
    assert format_cost_line(breakdown, include_reasoning=False) == (
        "Cost: 1.9¢ (0.4¢ input, 1.5¢ output)"
    )


def test_compute_cost_breakdown_splits_reasoning_from_output() -> None:
    tokens = TokenBreakdown(input_tokens=1000, reasoning_tokens=500, output_tokens=2000)
    schedule = {"input": 2.0, "output": 8.0}
    breakdown = compute_cost_breakdown(
        tokens,
        schedule,
        output_includes_reasoning=True,
    )
    assert breakdown is not None
    assert breakdown.input_cost == pytest.approx(0.002)
    assert breakdown.reasoning_cost == pytest.approx(0.004)
    assert breakdown.output_cost == pytest.approx(0.012)
    assert breakdown.total_cost == pytest.approx(0.018)


def test_compute_cost_breakdown_keeps_output_separate() -> None:
    tokens = TokenBreakdown(input_tokens=1000, reasoning_tokens=500, output_tokens=2000)
    schedule = {"input": 2.0, "output": 8.0}
    breakdown = compute_cost_breakdown(
        tokens,
        schedule,
        output_includes_reasoning=False,
    )
    assert breakdown is not None
    assert breakdown.input_cost == pytest.approx(0.002)
    assert breakdown.reasoning_cost == pytest.approx(0.004)
    assert breakdown.output_cost == pytest.approx(0.016)
    assert breakdown.total_cost == pytest.approx(0.022)
