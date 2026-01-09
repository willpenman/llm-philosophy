"""Tests for OpenAI request assembly."""

from __future__ import annotations

from providers.openai import build_response_request, price_schedule_for_model  # noqa: E402


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


def test_price_schedule_for_model_includes_units() -> None:
    schedule = price_schedule_for_model("o3-2025-04-16")
    assert schedule is not None
    assert schedule["unit"] == "per_million_tokens"
    assert "input" in schedule
    assert "output" in schedule
