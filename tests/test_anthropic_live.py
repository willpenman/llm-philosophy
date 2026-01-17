"""Live Anthropic API tests.

Marked as live because they incur cost and require API access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from providers.anthropic import build_messages_request, send_messages_request  # noqa: E402

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
    if os.getenv("RUN_LIVE_ANTHROPIC") != "1":
        pytest.skip("Set RUN_LIVE_ANTHROPIC=1 to enable live Anthropic tests.")
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("Missing ANTHROPIC_API_KEY for live Anthropic tests.")


# ACCEPTS SYSTEM
@pytest.mark.live
@pytest.mark.parametrize("model", ["claude-opus-4-5-20251101", "claude-3-haiku-20240307"])
def test_anthropic_accepts_system_prompt_live(model: str) -> None:
    _skip_if_live_disabled()
    payload = build_messages_request(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=2048
    )
    response = send_messages_request(
        payload,
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )
    assert "OK" in response.output_text.upper()


# TEMPERATURE
@pytest.mark.live
@pytest.mark.parametrize("model", ["claude-opus-4-5-20251101"])
def test_anthropic_rejects_temperature_with_thinking_live(model: str) -> None:
    _skip_if_live_disabled()
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": [{"type": "text", "text": "System."}],
        "messages": [{"role": "user", "content": "User."}],
        "temperature": 0.2,
        "thinking": {"type": "enabled", "budget_tokens": 1024},
    }
    with pytest.raises(RuntimeError, match=r"temperature"):
        send_messages_request(
            payload,
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )


# THINKING
@pytest.mark.live
@pytest.mark.parametrize("model", ["claude-opus-4-5-20251101"])
def test_anthropic_accepts_thinking_live(model: str) -> None:
    _skip_if_live_disabled()
    payload = build_messages_request(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=2048,
        thinking={"type": "enabled", "budget_tokens": 1024},
    )
    response = send_messages_request(
        payload,
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )
    assert "OK" in response.output_text.upper()


@pytest.mark.live
@pytest.mark.parametrize("model", ["claude-3-haiku-20240307"])
def test_anthropic_rejects_thinking_live(model: str) -> None:
    _skip_if_live_disabled()
    payload = {
        "model": model,
        "max_tokens": 512,
        "system": [{"type": "text", "text": "System."}],
        "messages": [{"role": "user", "content": "User."}],
        "thinking": {"type": "enabled", "budget_tokens": 1024},
    }
    with pytest.raises(RuntimeError, match=r"thinking"):
        send_messages_request(
            payload,
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )


# MAX OUTPUT TOKENS
@pytest.mark.live
@pytest.mark.parametrize(
    ("model", "max_output_tokens"),
    [
        ("claude-opus-4-5-20251101", 64001),
        ("claude-3-haiku-20240307", 4501),
    ],
)
def test_anthropic_rejects_over_max_output_tokens_live(
    model: str, max_output_tokens: int
) -> None:
    _skip_if_live_disabled()
    payload = build_messages_request(
        system_prompt="System.",
        user_prompt="User.",
        model=model,
        max_output_tokens=max_output_tokens
    )
    with pytest.raises(RuntimeError, match=r"max_tokens"):
        send_messages_request(
            payload,
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )
