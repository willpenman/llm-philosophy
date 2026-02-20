"""Tests for Anthropic request assembly."""

from __future__ import annotations

import pytest

from src.providers.anthropic import (
    build_messages_request,
    calculate_cost_breakdown,
    display_model_name,
    extract_usage_breakdown,
    price_schedule_for_model,
)


def test_build_messages_request_includes_system_and_user() -> None:
    payload = build_messages_request(
        system_prompt="System text",
        user_prompt="User text",
        model="claude-opus-4-5-20251101",
        max_output_tokens=128,
    )
    assert payload["model"] == "claude-opus-4-5-20251101"
    assert payload["system"][0]["text"] == "System text"
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][0]["content"] == "User text"


def test_build_messages_request_uses_default_max_output_tokens() -> None:
    payload = build_messages_request(
        system_prompt="System text",
        user_prompt="User text",
        model="claude-opus-4-6",
        max_output_tokens=None,
    )
    assert payload["max_tokens"] == 128000

    payload = build_messages_request(
        system_prompt="System text",
        user_prompt="User text",
        model="claude-sonnet-4-6",
        max_output_tokens=None,
    )
    assert payload["max_tokens"] == 64000

    payload = build_messages_request(
        system_prompt="System text",
        user_prompt="User text",
        model="claude-opus-4-5-20251101",
        max_output_tokens=None,
    )
    assert payload["max_tokens"] == 64000

    payload = build_messages_request(
        system_prompt="System text",
        user_prompt="User text",
        model="claude-3-haiku-20240307",
        max_output_tokens=None,
    )
    assert payload["max_tokens"] == 4000


def test_build_messages_request_includes_optional_params() -> None:
    payload = build_messages_request(
        system_prompt="System text",
        user_prompt="User text",
        model="claude-opus-4-5-20251101",
        max_output_tokens=128,
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        thinking=None,
        output_config={"effort": "max"},
        stream=True,
    )
    assert payload["temperature"] == 0.2
    assert payload["top_p"] == 0.95
    assert payload["top_k"] == 40
    assert payload["output_config"] == {"effort": "max"}
    assert payload["stream"] is True


@pytest.mark.parametrize(
    ("model", "thinking", "error"),
    [
        ("claude-opus-4-5-20251101", {"type": "disabled", "budget_tokens": 1000}, "thinking.type"),
        ("claude-opus-4-5-20251101", {"type": "enabled", "budget_tokens": "1000"}, "budget_tokens"),
        ("claude-opus-4-5-20251101", {"type": "enabled", "budget_tokens": 0}, "budget_tokens"),
        ("claude-opus-4-5-20251101", {"type": "enabled", "budget_tokens": 128}, "budget_tokens"),
        ("claude-opus-4-6", {"type": "adaptive", "budget_tokens": 10}, "budget_tokens"),
        ("claude-opus-4-6", {"type": "adaptive", "effort": 123}, "effort"),
    ],
)
def test_build_messages_request_rejects_invalid_thinking_config(
    model: str, thinking: dict[str, object], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        build_messages_request(
            system_prompt="System text",
            user_prompt="User text",
            model=model,
            max_output_tokens=128,
            thinking=thinking,
        )


def test_build_messages_request_rejects_adaptive_thinking_for_manual_model() -> None:
    with pytest.raises(ValueError, match="adaptive"):
        build_messages_request(
            system_prompt="System text",
            user_prompt="User text",
            model="claude-opus-4-5-20251101",
            max_output_tokens=128,
            thinking={"type": "adaptive"},
        )


def test_build_messages_request_accepts_adaptive_thinking_for_opus_46() -> None:
    payload = build_messages_request(
        system_prompt="System text",
        user_prompt="User text",
        model="claude-opus-4-6",
        max_output_tokens=128,
        thinking={"type": "adaptive"},
    )
    assert payload["thinking"] == {"type": "adaptive"}


def test_build_messages_request_accepts_adaptive_thinking_for_sonnet_46() -> None:
    payload = build_messages_request(
        system_prompt="System text",
        user_prompt="User text",
        model="claude-sonnet-4-6",
        max_output_tokens=128,
        thinking={"type": "adaptive"},
    )
    assert payload["thinking"] == {"type": "adaptive"}


def test_build_messages_request_accepts_temperature_for_opus_46() -> None:
    payload = build_messages_request(
        system_prompt="System text",
        user_prompt="User text",
        model="claude-opus-4-6",
        max_output_tokens=128,
        temperature=0.2,
    )
    assert payload["temperature"] == 0.2


def test_build_messages_request_rejects_temperature_for_sonnet_46() -> None:
    with pytest.raises(ValueError, match="temperature"):
        build_messages_request(
            system_prompt="System text",
            user_prompt="User text",
            model="claude-sonnet-4-6",
            max_output_tokens=128,
            temperature=0.2,
        )


@pytest.mark.parametrize(
    ("model", "alias", "input_cost", "output_cost"),
    [
        ("claude-opus-4-6", "Claude Opus 4.6", 5.0, 25.0),
        ("claude-sonnet-4-6", "Claude Sonnet 4.6", 3.0, 15.0),
        ("claude-opus-4-5-20251101", "Claude Opus 4.5", 5.0, 25.0),
        ("claude-3-haiku-20240307", "Claude Haiku 3", 0.25, 1.25),
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


def test_extract_usage_breakdown_reads_anthropic_usage() -> None:
    payload = {
        "usage": {
            "input_tokens": 10,
            "cache_creation_input_tokens": 2,
            "cache_read_input_tokens": 3,
            "output_tokens": 20,
        }
    }
    breakdown = extract_usage_breakdown(payload)
    assert breakdown is not None
    assert breakdown.input_tokens == 15
    assert breakdown.output_tokens == 20
    assert breakdown.reasoning_tokens is None


def test_calculate_cost_breakdown_uses_anthropic_rates() -> None:
    payload = {
        "usage": {
            "input_tokens": 10,
            "cache_creation_input_tokens": 2,
            "cache_read_input_tokens": 3,
            "output_tokens": 20,
        }
    }
    breakdown = calculate_cost_breakdown(payload, model="claude-opus-4-5-20251101")
    assert breakdown is not None
    assert breakdown.input_cost == pytest.approx(0.000075)
    assert breakdown.reasoning_cost == pytest.approx(0.0)
    assert breakdown.output_cost == pytest.approx(0.0005)
    assert breakdown.total_cost == pytest.approx(0.000575)
