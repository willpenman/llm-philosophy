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


# SYSTEM PROMPT
@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-2.0-flash-lite-001"])
def test_gemini_accepts_system_prompt_live(model: str) -> None:
    _skip_if_live_disabled()
    response = create_response(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=16,
    )
    assert "OK" in response.output_text.upper()


# TEMPERATURE, TOP_P, TOP_K
@pytest.mark.live
@pytest.mark.parametrize("model", ["gemini-2.0-flash-lite-001"])
def test_gemini_accepts_sampling_params_live(model: str) -> None:
    _skip_if_live_disabled()
    response = create_response(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=16,
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
        max_output_tokens=16,
    )
    payload["config"]["thinking_config"] = {"thinking_level": "MEDIUM"}
    with pytest.raises(RuntimeError):
        send_generate_content_request(payload)


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
