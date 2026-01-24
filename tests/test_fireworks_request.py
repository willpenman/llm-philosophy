"""Tests for Fireworks request assembly."""

from __future__ import annotations

import pytest

from src.providers.fireworks import (  # noqa: E402
    build_response_request,
    calculate_cost_breakdown,
    display_model_name,
    display_provider_name,
    extract_usage_breakdown,
    price_schedule_for_model,
    provider_for_model,
)


def test_build_response_request_includes_system_and_user() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="accounts/fireworks/models/deepseek-v3p2",
        max_output_tokens=16,
    )
    assert payload["model"] == "accounts/fireworks/models/deepseek-v3p2"
    assert payload["input"][0]["role"] == "system"
    assert payload["input"][1]["role"] == "user"


def test_build_response_request_uses_default_max_output_tokens() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="accounts/fireworks/models/deepseek-v3p2",
        max_output_tokens=None,
    )
    assert payload["max_output_tokens"] == 64000


def test_build_response_request_includes_temperature_top_p_when_set() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="accounts/fireworks/models/deepseek-v3p2",
        max_output_tokens=32,
        temperature=0.2,
        top_p=0.9,
    )
    assert payload["temperature"] == 0.2
    assert payload["top_p"] == 0.9


def test_price_schedule_for_model_includes_units() -> None:
    schedule = price_schedule_for_model("accounts/fireworks/models/deepseek-v3p2")
    assert schedule is not None
    assert schedule["unit"] == "per_million_tokens"
    assert schedule["input"] == 0.56
    assert schedule["output"] == 1.68
    assert display_model_name("accounts/fireworks/models/deepseek-v3p2") == "DeepSeek V3.2"


def test_provider_for_model_uses_maker() -> None:
    provider = provider_for_model("accounts/fireworks/models/deepseek-v3p2")
    assert provider == "deepseek"
    assert display_provider_name(provider) == "DeepSeek AI"


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
        payload, model="accounts/fireworks/models/deepseek-v3p2"
    )
    assert breakdown is not None
    assert breakdown.input_cost == pytest.approx(0.0000056)
    assert breakdown.reasoning_cost == pytest.approx(0.0)
    assert breakdown.output_cost == pytest.approx(0.0000504)
    assert breakdown.total_cost == pytest.approx(0.000056)
