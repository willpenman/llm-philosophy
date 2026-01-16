"""Live Gemini API tests.

Marked as live because they incur cost and require API access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from providers.gemini import (  # noqa: E402
    build_generate_content_request,
    create_response,
    send_generate_content_request,
)

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
    if os.getenv("RUN_LIVE_GEMINI") != "1":
        pytest.skip("Set RUN_LIVE_GEMINI=1 to enable live Gemini tests.")
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        pytest.skip("Missing GEMINI_API_KEY or GOOGLE_API_KEY for live Gemini tests.")
    try:
        import google.genai  # noqa: F401
    except ModuleNotFoundError:
        pytest.skip("google-genai not installed; install it to run live Gemini tests.")


def _has_thoughts(payload: dict[str, object]) -> bool:
    usage = payload.get("usage_metadata")
    if isinstance(usage, dict):
        thoughts_count = usage.get("thoughts_token_count")
        if isinstance(thoughts_count, int) and thoughts_count > 0:
            return True
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return False
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict):
                continue
            thought = part.get("thought")
            if isinstance(thought, str) and thought.strip():
                return True
    return False


# SYSTEM PROMPT
@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-2.0-flash-lite-001", "gemini-3-pro-preview"])
def test_gemini_accepts_system_prompt_live(model: str) -> None:
    _skip_if_live_disabled()
    max_output_tokens = 150 if model == "gemini-3-pro-preview" else 16
    response = create_response(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=max_output_tokens,
    )
    assert "OK" in response.output_text.upper()


# TEMPERATURE, TOP_P, TOP_K
@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-2.0-flash-lite-001", "gemini-3-pro-preview"])
def test_gemini_accepts_sampling_params_live(model: str) -> None:
    _skip_if_live_disabled()
    max_output_tokens = 150 if model == "gemini-3-pro-preview" else 16
    response = create_response(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=0.2,
        top_p=0.9,
        top_k=40,
    )
    assert "OK" in response.output_text.upper()


# REASONING
@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-2.0-flash-lite-001"])
def test_gemini_rejects_thinking_config_live(model: str) -> None:
    _skip_if_live_disabled()
    payload = build_generate_content_request(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=150,
    )
    payload["config"]["thinking_config"] = {"thinking_level": "MEDIUM"}
    with pytest.raises(RuntimeError):
        send_generate_content_request(payload)


@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-3-pro-preview"])
@pytest.mark.parametrize("thinking_level", ["LOW", "HIGH"])
def test_gemini_accepts_thinking_levels_live(
    model: str, thinking_level: str
) -> None:
    _skip_if_live_disabled()
    payload = build_generate_content_request(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=150,
    )
    payload["config"]["thinking_config"] = {"thinking_level": thinking_level}
    response = send_generate_content_request(payload)
    assert "OK" in response.output_text.upper()


@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-3-pro-preview"])
def test_gemini_accepts_thinking_budget_live(model: str) -> None:
    _skip_if_live_disabled()
    payload = build_generate_content_request(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=16,
    )
    payload["config"]["thinking_config"] = {"thinking_budget": 256}
    response = send_generate_content_request(payload)
    assert "OK" in response.output_text.upper()


@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-3-pro-preview"])
def test_gemini_include_thoughts_returns_payload_live(model: str) -> None:
    _skip_if_live_disabled()
    payload = build_generate_content_request(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=3000,  # failed on 1000, reached max tokens
    )
    payload["config"]["thinking_config"] = {
        "thinking_level": "HIGH",
        "include_thoughts": True,
    }
    response = send_generate_content_request(payload)
    assert "OK" in response.output_text.upper()
    assert _has_thoughts(response.payload)


# MAX OUTPUT
@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-2.0-flash-lite-001"])
def test_gemini_accepts_max_output_tokens_8192_live(model: str) -> None:
    _skip_if_live_disabled()
    response = create_response(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=8192,
    )
    assert "OK" in response.output_text.upper()


# STREAMING
@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-2.0-flash-lite-001", "gemini-3-pro-preview"])
def test_gemini_streaming_captures_long_output_live(model: str) -> None:
    _skip_if_live_disabled()
    response = create_response(
        system_prompt="You are a test harness. Follow the user's instructions.",
        user_prompt=(
            "Write a response of about 300 words about the "
            "philosophical implications of model introspection. End with the word END."
        ),
        model=model,
        max_output_tokens=4000,
        stream=True,
    )
    assert response.output_text.strip().endswith("END")
    assert len(response.output_text) > 100
