"""Tests for OpenAI request assembly."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from providers.openai import build_response_request  # noqa: E402


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
