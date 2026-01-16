"""Tests for Gemini request assembly."""

from __future__ import annotations

from providers.gemini import (
    build_generate_content_request,
    display_model_name,
    price_schedule_for_model,
)


def test_build_generate_content_request_includes_system_and_user() -> None:
    payload = build_generate_content_request(
        system_prompt="System text",
        user_prompt="User text",
        model="gemini-2.0-flash-lite-001",
    )
    assert payload["model"] == "gemini-2.0-flash-lite-001"
    assert payload["contents"] == "User text"
    assert payload["config"]["system_instruction"] == "System text"


def test_build_generate_content_request_includes_optional_params() -> None:
    payload = build_generate_content_request(
        system_prompt="System text",
        user_prompt="User text",
        model="gemini-2.0-flash-lite-001",
        max_output_tokens=128,
        temperature=0.2,
        top_p=0.9,
        top_k=40,
        tools=[{"type": "function", "name": "noop"}],
    )
    assert payload["config"]["max_output_tokens"] == 128
    assert payload["config"]["temperature"] == 0.2
    assert payload["config"]["top_p"] == 0.9
    assert payload["config"]["top_k"] == 40
    assert payload["config"]["tools"][0]["name"] == "noop"


def test_build_generate_content_request_omits_empty_tools() -> None:
    payload = build_generate_content_request(
        system_prompt="System text",
        user_prompt="User text",
        model="gemini-2.0-flash-lite-001",
        tools=[],
    )
    assert "tools" not in payload["config"]


def test_price_schedule_for_model_includes_units() -> None:
    schedule = price_schedule_for_model("gemini-2.0-flash-lite-001")
    assert schedule is not None
    assert schedule["unit"] == "per_million_tokens"
    assert schedule["input"] == 0.075
    assert schedule["output"] == 0.30
    assert display_model_name("gemini-2.0-flash-lite-001") == "2.0 Flash Lite"
