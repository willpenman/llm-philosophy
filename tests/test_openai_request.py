"""Tests for OpenAI request assembly."""

from __future__ import annotations

import pytest

from src.providers.openai import (  # noqa: E402
    build_response_request,
    calculate_cost_breakdown,
    display_model_name,
    extract_usage_breakdown,
    price_schedule_for_model,
)


def test_build_response_request_includes_system_and_user() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="o3-2025-04-16",
        max_output_tokens=16,
    )
    assert payload["model"] == "o3-2025-04-16"
    assert payload["input"][0]["role"] == "system"
    assert payload["input"][1]["role"] == "user"


def test_build_response_request_supports_o3_parameters() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="o3-2025-04-16",
        max_output_tokens=None,
        reasoning={"effort": "medium", "summary": "auto"},
        tools=[
            {
                "type": "function",
                "name": "noop",
                "description": "No-op tool.",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
        tool_choice="auto",
    )

    assert payload["max_output_tokens"] == 100000
    assert payload["reasoning"]["effort"] == "medium"
    assert payload["tools"][0]["name"] == "noop"
    assert payload["tool_choice"] == "auto"


def test_build_response_request_uses_gpt52_default_max_output_tokens() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="gpt-5.2-2025-12-11",
        max_output_tokens=None,
    )
    assert payload["max_output_tokens"] == 128000


def test_build_response_request_uses_gpt4o_default_max_output_tokens() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="gpt-4o-2024-05-13",
        max_output_tokens=None,
    )
    assert payload["max_output_tokens"] == 64000


def test_build_response_request_uses_gpt4_0613_default_max_output_tokens() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="gpt-4-0613",
        max_output_tokens=None,
    )
    assert payload["max_output_tokens"] == 8192


def test_build_response_request_includes_temperature_when_set() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="dummy-model",
        max_output_tokens=8,
        temperature=0.2,
    )
    assert payload["temperature"] == 0.2


def test_build_response_request_includes_top_p_when_set() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="dummy-model",
        max_output_tokens=8,
        top_p=0.9,
    )
    assert payload["top_p"] == 0.9


def test_build_response_request_omits_empty_tools() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="o3-2025-04-16",
        max_output_tokens=16,
        tools=[],
    )
    assert "tools" not in payload


def test_build_response_request_includes_streaming_flags() -> None:
    payload = build_response_request(
        system_prompt="System text",
        user_prompt="User text",
        model="o3-2025-04-16",
        max_output_tokens=16,
        stream=True,
        stream_options={"include_obfuscation": False},
    )
    assert payload["stream"] is True
    assert payload["stream_options"]["include_obfuscation"] is False


@pytest.mark.parametrize(
    ("model", "alias", "input_cost", "output_cost"),
    [
        ("o3-2025-04-16", "o3", 2.0, 8.0),
        ("gpt-4o-2024-05-13", "4o", 2.5, 10.0),
        ("gpt-5.2-2025-12-11", "GPT 5.2", 1.75, 14.0),
        ("gpt-4-0613", "GPT-4 update 1", 30.0, 60.0),
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


def test_extract_usage_breakdown_reads_openai_usage() -> None:
    payload = {
        "usage": {
            "input_tokens": 12,
            "output_tokens": 34,
            "output_tokens_details": {"reasoning_tokens": 5},
        }
    }
    breakdown = extract_usage_breakdown(payload)
    assert breakdown is not None
    assert breakdown.input_tokens == 12
    assert breakdown.output_tokens == 34
    assert breakdown.reasoning_tokens == 5


def test_calculate_cost_breakdown_uses_openai_rates() -> None:
    payload = {
        "usage": {
            "input_tokens": 10,
            "output_tokens": 30,
            "output_tokens_details": {"reasoning_tokens": 5},
        }
    }
    breakdown = calculate_cost_breakdown(payload, model="o3-2025-04-16")
    assert breakdown is not None
    assert breakdown.input_cost == pytest.approx(0.00002)
    assert breakdown.reasoning_cost == pytest.approx(0.00004)
    assert breakdown.output_cost == pytest.approx(0.0002)
    assert breakdown.total_cost == pytest.approx(0.00026)
