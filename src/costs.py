"""Cost and token breakdown utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TokenBreakdown:
    input_tokens: int | None
    reasoning_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True)
class CostBreakdown:
    input_cost: float
    reasoning_cost: float
    output_cost: float
    total_cost: float


def compute_cost_breakdown(
    tokens: TokenBreakdown,
    price_schedule: dict[str, Any],
    *,
    output_includes_reasoning: bool,
) -> CostBreakdown | None:
    input_rate = price_schedule.get("input")
    output_rate = price_schedule.get("output")
    if not isinstance(input_rate, (int, float)) or not isinstance(output_rate, (int, float)):
        return None
    if not isinstance(tokens.input_tokens, int) or not isinstance(tokens.output_tokens, int):
        return None
    reasoning_tokens = tokens.reasoning_tokens if isinstance(tokens.reasoning_tokens, int) else 0
    output_tokens = tokens.output_tokens
    if output_includes_reasoning:
        output_tokens = max(output_tokens - reasoning_tokens, 0)
    input_cost = tokens.input_tokens * (float(input_rate) / 1_000_000)
    reasoning_cost = reasoning_tokens * (float(output_rate) / 1_000_000)
    output_cost = output_tokens * (float(output_rate) / 1_000_000)
    total_cost = input_cost + reasoning_cost + output_cost
    return CostBreakdown(
        input_cost=input_cost,
        reasoning_cost=reasoning_cost,
        output_cost=output_cost,
        total_cost=total_cost,
    )


def format_cost(value: float) -> str:
    if value < 0.001:
        return "rounds to 0¢"
    if value < 1:
        return f"{value * 100:.1f}¢"
    return f"${value:.2f}"


def format_cost_line(
    breakdown: CostBreakdown,
    *,
    output_label: str = "output",
    include_reasoning: bool = True,
) -> str:
    total_label = format_cost(breakdown.total_cost)
    if total_label == "rounds to 0¢":
        return f"Cost: {total_label}"
    input_label = format_cost(breakdown.input_cost)
    output_cost_label = format_cost(breakdown.output_cost)
    if not include_reasoning:
        return (
            "Cost: "
            f"{total_label} ({input_label} input, {output_cost_label} {output_label})"
        )
    reasoning_label = format_cost(breakdown.reasoning_cost)
    return (
        "Cost: "
        f"{total_label} ({input_label} input, {reasoning_label} reasoning, {output_cost_label} {output_label})"
    )
