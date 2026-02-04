"""Tests for Fireworks request assembly."""

from __future__ import annotations

import pytest

from src.providers.fireworks import (  # noqa: E402
    build_chat_completion_request,
    calculate_cost_breakdown,
    display_model_name,
    display_provider_name,
    extract_usage_breakdown,
    price_schedule_for_model,
    provider_for_model,
)


def test_build_chat_completion_request_includes_system_and_user() -> None:
    payload = build_chat_completion_request(
        system_prompt="System text",
        user_prompt="User text",
        model="deepseek-v3p2",
        max_output_tokens=16,
    )
    assert payload["model"] == "accounts/fireworks/models/deepseek-v3p2"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"
    assert payload["max_tokens"] == 16


@pytest.mark.parametrize(
    ("model", "expected_max_tokens"),
    [
        ("deepseek-v3p2", 64000),
        ("deepseek-v3-0324", 30000),
        ("qwen3-vl-235b-thinking", 38912),
        ("qwen2p5-vl-32b", 128000),
    ],
)
def test_build_chat_completion_request_uses_default_max_output_tokens(
    model: str, expected_max_tokens: int
) -> None:
    payload = build_chat_completion_request(
        system_prompt="System text",
        user_prompt="User text",
        model=model,
        max_output_tokens=None,
    )
    assert payload["max_tokens"] == expected_max_tokens


def test_build_chat_completion_request_includes_temperature_top_p_when_set() -> None:
    payload = build_chat_completion_request(
        system_prompt="System text",
        user_prompt="User text",
        model="deepseek-v3p2",
        max_output_tokens=32,
        temperature=0.2,
        top_p=0.9,
    )
    assert payload["temperature"] == 0.2
    assert payload["top_p"] == 0.9


@pytest.mark.parametrize(
    ("model", "expected_input", "expected_output", "expected_alias"),
    [
        ("deepseek-v3p2", 0.56, 1.68, "DeepSeek V3.2"),
        ("deepseek-v3-0324", 0.90, 0.90, "DeepSeek V3 Update 1"),
        ("qwen3-vl-235b-thinking", 0.22, 0.88, "Qwen3-VL 235B Thinking"),
        ("qwen2p5-vl-32b", 0.90, 0.90, "Qwen2.5-VL 32B"),
    ],
)
def test_price_schedule_for_model_includes_units(
    model: str,
    expected_input: float,
    expected_output: float,
    expected_alias: str,
) -> None:
    schedule = price_schedule_for_model(model)
    assert schedule is not None
    assert schedule["unit"] == "per_million_tokens"
    assert schedule["input"] == expected_input
    assert schedule["output"] == expected_output
    assert display_model_name(model) == expected_alias


@pytest.mark.parametrize(
    ("model", "expected_provider", "expected_provider_alias"),
    [
        ("deepseek-v3p2", "deepseek", "DeepSeek AI (via Fireworks)"),
        ("deepseek-v3-0324", "deepseek", "DeepSeek AI (via Fireworks)"),
        ("qwen3-vl-235b-thinking", "qwen", "Qwen (via Fireworks)"),
        ("qwen2p5-vl-32b", "qwen", "Qwen (via Fireworks)"),
    ],
)
def test_provider_for_model_uses_maker(
    model: str, expected_provider: str, expected_provider_alias: str
) -> None:
    provider = provider_for_model(model)
    assert provider == expected_provider
    assert display_provider_name(provider) == expected_provider_alias


def test_extract_usage_breakdown_reads_fireworks_usage() -> None:
    payload = {
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 34,
            "total_tokens": 46,
        }
    }
    breakdown = extract_usage_breakdown(payload)
    assert breakdown is not None
    assert breakdown.input_tokens == 12
    assert breakdown.output_tokens == 34
    assert breakdown.reasoning_tokens is None


def test_calculate_cost_breakdown_uses_fireworks_rates() -> None:
    payload = {
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 30,
            "total_tokens": 40,
        }
    }
    breakdown = calculate_cost_breakdown(
        payload, model="deepseek-v3p2"
    )
    assert breakdown is not None
    assert breakdown.input_cost == pytest.approx(0.0000056)
    assert breakdown.reasoning_cost == pytest.approx(0.0)
    assert breakdown.output_cost == pytest.approx(0.0000504)
    assert breakdown.total_cost == pytest.approx(0.000056)


def test_calculate_cost_breakdown_uses_v3_0324_rates() -> None:
    payload = {
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 30,
            "total_tokens": 40,
        }
    }
    breakdown = calculate_cost_breakdown(
        payload, model="deepseek-v3-0324"
    )
    assert breakdown is not None
    assert breakdown.input_cost == pytest.approx(0.000009)
    assert breakdown.reasoning_cost == pytest.approx(0.0)
    assert breakdown.output_cost == pytest.approx(0.000027)
    assert breakdown.total_cost == pytest.approx(0.000036)
