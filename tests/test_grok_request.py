"""Tests for Grok request assembly."""

from __future__ import annotations

import pytest

from src.providers.grok import (
    build_chat_completion_request,
    calculate_cost_breakdown,
    display_model_name,
    extract_usage_breakdown,
    price_schedule_for_model,
)


def test_build_chat_completion_request_includes_system_and_user() -> None:
    payload = build_chat_completion_request(
        system_prompt="System text",
        user_prompt="User text",
        model="grok-4-1-fast-reasoning",
    )
    assert payload["model"] == "grok-4-1-fast-reasoning"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"


def test_build_chat_completion_request_includes_optional_params() -> None:
    payload = build_chat_completion_request(
        system_prompt="System text",
        user_prompt="User text",
        model="grok-4-1-fast-reasoning",
        max_output_tokens=128,
        temperature=0.2,
        top_p=0.9,
        stream=True,
    )
    assert payload["max_tokens"] == 128
    assert payload["temperature"] == 0.2
    assert payload["top_p"] == 0.9
    assert payload["stream"] is True


@pytest.mark.parametrize(
    ("model", "alias", "input_cost", "output_cost"),
    [
        ("grok-4-1-fast-reasoning", "Grok 4.1 Fast Reasoning", 0.20, 0.50),
    ],
)
def test_price_schedule_for_model_includes_units(
    model: str,
    alias: str,
    input_cost: float,
    output_cost: float,
) -> None:
    schedule = price_schedule_for_model(model)
    assert schedule is not None
    assert schedule["unit"] == "per_million_tokens"
    assert schedule["input"] == input_cost
    assert schedule["output"] == output_cost
    assert display_model_name(model) == alias


def test_extract_usage_breakdown_reads_grok_usage() -> None:
    payload = {
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 25,
            "prompt_tokens_details": {
                "text_tokens": 15,
                "audio_tokens": 0,
                "image_tokens": 0,
                "cached_tokens": 3,
            },
            "completion_tokens_details": {"reasoning_tokens": 5},
        }
    }
    breakdown = extract_usage_breakdown(payload)
    assert breakdown is not None
    assert breakdown.input_tokens == 15
    assert breakdown.output_tokens == 25
    assert breakdown.reasoning_tokens == 5


def test_calculate_cost_breakdown_uses_grok_rates() -> None:
    payload = {
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 30,
            "completion_tokens_details": {"reasoning_tokens": 5},
        }
    }
    breakdown = calculate_cost_breakdown(payload, model="grok-4-1-fast-reasoning")
    assert breakdown is not None
    assert breakdown.input_cost == pytest.approx(0.000002)
    assert breakdown.reasoning_cost == pytest.approx(0.0000025)
    assert breakdown.output_cost == pytest.approx(0.0000125)
    assert breakdown.total_cost == pytest.approx(0.000017)
