"""Live Fireworks API tests.

Marked as live because they incur cost and require API access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.providers.fireworks import create_response  # noqa: E402

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
    if os.getenv("RUN_LIVE_FIREWORKS") != "1":
        pytest.skip("Set RUN_LIVE_FIREWORKS=1 to enable live Fireworks tests.")
    if not os.getenv("FIREWORKS_API_KEY"):
        pytest.skip("Missing FIREWORKS_API_KEY for live Fireworks tests.")


@pytest.mark.live
def test_fireworks_accepts_system_prompt_live() -> None:
    _skip_if_live_disabled()
    response = create_response(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model="deepseek-v3p2",
        max_output_tokens=16,
    )
    assert "OK" in response.output_text.upper()


@pytest.mark.live
def test_fireworks_streaming_captures_output_live() -> None:
    _skip_if_live_disabled()
    response = create_response(
        system_prompt="You are a test harness. Follow the user's instructions.",
        user_prompt=(
            "Write a short paragraph about model introspection. "
            "End with the word END."
        ),
        model="deepseek-v3p2",
        max_output_tokens=512,
        stream=True,
    )
    assert response.output_text.strip().endswith("END")
