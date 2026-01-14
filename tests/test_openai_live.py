"""Live OpenAI API tests.

Marked as live because they incur cost and require API access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from providers.openai import create_response  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv_if_present() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _skip_if_live_disabled() -> None:
    _load_dotenv_if_present()
    if os.getenv("RUN_LIVE_OPENAI") != "1":
        pytest.skip("Set RUN_LIVE_OPENAI=1 to enable live OpenAI tests.")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("Missing OPENAI_API_KEY for live OpenAI tests.")


def _create_response_or_skip_on_server_error(**kwargs):
    try:
        return create_response(**kwargs)
    except RuntimeError as exc:
        message = str(exc)
        if "server_error" in message or "Internal Server Error" in message:
            pytest.skip("OpenAI server error; retry live test.")
        raise


# ACCEPTS SYSTEM
@pytest.mark.live
@pytest.mark.parametrize("model", ["o3-2025-04-16", "gpt-4o-2024-05-13"])
def test_openai_accepts_system_prompt_live(model: str) -> None:
    _skip_if_live_disabled()
    response = _create_response_or_skip_on_server_error(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=16,
    )
    assert "OK" in response.output_text.upper()


# TEMPERATURE AND TOP_P
@pytest.mark.live
@pytest.mark.parametrize("model", ["gpt-4o-2024-05-13"])
def test_openai_accepts_temperature_top_p_live(model: str) -> None:
    _skip_if_live_disabled()
    response = _create_response_or_skip_on_server_error(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=16,
        temperature=0.2,
        top_p=0.9,
    )
    assert "OK" in response.output_text.upper()

@pytest.mark.live
@pytest.mark.parametrize("model", ["o3-2025-04-16"])
def test_openai_rejects_top_p_live(model: str) -> None:
    _skip_if_live_disabled()
    with pytest.raises(RuntimeError, match=r"top_p"):
        create_response(
            system_prompt="System.",
            user_prompt="User.",
            model=model,
            max_output_tokens=16,
            top_p=0.9,
        )

@pytest.mark.live
@pytest.mark.parametrize("model", ["o3-2025-04-16"])
def test_openai_rejects_temperature_live(model: str) -> None:
    _skip_if_live_disabled()
    with pytest.raises(RuntimeError, match=r"Unsupported parameter: 'temperature'"):
        create_response(
            system_prompt="System.",
            user_prompt="User.",
            model=model,
            max_output_tokens=16,
            temperature=0.2,
        )


# REASONING
@pytest.mark.live
@pytest.mark.parametrize("model", ["o3-2025-04-16", "gpt-4o-2024-05-13"])
def test_openai_accepts_tools_live(model: str) -> None:
    _skip_if_live_disabled()
    response = _create_response_or_skip_on_server_error(
        system_prompt="You are a test harness.",
        user_prompt="Reply by using the noop tool, use property 'OK'.",
        model=model,
        max_output_tokens=30,
        tools=[
            {
                "type": "function",
                "name": "noop",
                "description": "No-op tool.",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
        tool_choice="required",
    )
    assert isinstance(response.output_text, str)

@pytest.mark.live
@pytest.mark.parametrize("effort", ["low", "medium", "high"])
@pytest.mark.parametrize("model", ["o3-2025-04-16"])
def test_openai_accepts_reasoning_effort_live(model: str, effort: str) -> None:
    _skip_if_live_disabled()
    response = _create_response_or_skip_on_server_error(
        system_prompt="System.",
        user_prompt="User.",
        model=model,
        max_output_tokens=16,
        reasoning={"effort": effort},
    )
    assert isinstance(response.output_text, str)
    
@pytest.mark.live
@pytest.mark.parametrize("model", ["gpt-4o-2024-05-13"])
def test_openai_rejects_reasoning_live(model: str) -> None:
    _skip_if_live_disabled()
    with pytest.raises(RuntimeError, match=r"reasoning"):
        create_response(
            system_prompt="System.",
            user_prompt="User.",
            model=model,
            max_output_tokens=16,
            reasoning={"effort": "medium"},
        )

@pytest.mark.live
@pytest.mark.parametrize("effort", ["none", "minimal", "xhigh"])
@pytest.mark.parametrize("model", ["o3-2025-04-16"])
def test_openai_rejects_invalid_reasoning_effort_live(model: str, effort: str) -> None:
    _skip_if_live_disabled()
    try:
        create_response(
            system_prompt="System.",
            user_prompt="User.",
            model=model,
            max_output_tokens=16,
            reasoning={"effort": effort},
        )
    except RuntimeError as exc:
        message = str(exc)
        if "server_error" in message or "Internal Server Error" in message:
            pytest.skip("OpenAI server error; retry live test.")
        if "reasoning" not in message and "reasoning.effort" not in message:
            raise
    else:
        raise AssertionError("Expected reasoning.effort to be rejected.")

# MAX OUTPUT TOKENS
# max output tokens seems to not throw an error when too high, this "should" be an error
@pytest.mark.live
@pytest.mark.parametrize("model", ["o3-2025-04-16"])
def test_openai_accepts_high_max_output_tokens_live(model: str) -> None:
    _skip_if_live_disabled()
    response = _create_response_or_skip_on_server_error(
        system_prompt="System.",
        user_prompt="User.",
        model=model,
        max_output_tokens=1000001,
    )
    assert isinstance(response.output_text, str)

@pytest.mark.live
@pytest.mark.parametrize("model", ["o3-2025-04-16"])
def test_openai_rejects_too_low_max_output_tokens_live(model: str) -> None:
    _skip_if_live_disabled()
    try:
        create_response(
            system_prompt="System.",
            user_prompt="User.",
            model=model,
            max_output_tokens=1,
        )
    except RuntimeError as exc:
        message = str(exc)
        if "server_error" in message or "Internal Server Error" in message:
            pytest.skip("OpenAI server error; retry live test.")
        if "max_output_tokens" not in message:
            raise
    else:
        raise AssertionError("Expected max_output_tokens to be rejected.")


# STREAMING
@pytest.mark.live
@pytest.mark.parametrize("model", ["o3-2025-04-16", "gpt-4o-2024-05-13"])
def test_openai_streaming_captures_long_output_live(model: str) -> None:
    _skip_if_live_disabled()
    response = _create_response_or_skip_on_server_error(
        system_prompt="You are a test harness. Follow the user's instructions.",
        user_prompt=(
            "Write a long, continuous response of about 300 words about the "
            "philosophical implications of model introspection. End with the word END."
        ),
        model=model,
        max_output_tokens=4000,
        stream=True,
        stream_options={"include_obfuscation": False},
    )
    assert response.output_text.strip().endswith("END")
    assert len(response.output_text) > 100
