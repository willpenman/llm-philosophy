"""Live OpenAI API tests.

Marked as live because they incur cost and require API access.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from providers.openai import create_response  # noqa: E402


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


@pytest.mark.live
def test_openai_o3_reasoning_and_tools_live() -> None:
    _skip_if_live_disabled()
    response = _create_response_or_skip_on_server_error(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model="o3-2025-04-16",
        max_output_tokens=16,
        reasoning={"effort": "medium"},
        tools=[
            {
                "type": "function",
                "name": "noop",
                "description": "No-op tool.",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
        tool_choice="none",
    )
    assert isinstance(response.output_text, str)


@pytest.mark.live
def test_openai_o3_rejects_temperature_live() -> None:
    _skip_if_live_disabled()
    with pytest.raises(RuntimeError, match=r"Unsupported parameter: 'temperature'"):
        create_response(
            system_prompt="System.",
            user_prompt="User.",
            model="o3-2025-04-16",
            max_output_tokens=16,
            temperature=0.2,
        )


@pytest.mark.live
def test_openai_o3_rejects_top_p_live() -> None:
    _skip_if_live_disabled()
    with pytest.raises(RuntimeError, match=r"top_p"):
        create_response(
            system_prompt="System.",
            user_prompt="User.",
            model="o3-2025-04-16",
            max_output_tokens=16,
            top_p=0.9,
        )


@pytest.mark.live
def test_openai_o3_accepts_high_max_output_tokens_live() -> None:
    _skip_if_live_disabled()
    response = _create_response_or_skip_on_server_error(
        system_prompt="System.",
        user_prompt="User.",
        model="o3-2025-04-16",
        max_output_tokens=100001,
    )
    assert isinstance(response.output_text, str)


@pytest.mark.live
@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_openai_o3_accepts_reasoning_effort_live(effort: str) -> None:
    _skip_if_live_disabled()
    response = _create_response_or_skip_on_server_error(
        system_prompt="System.",
        user_prompt="User.",
        model="o3-2025-04-16",
        max_output_tokens=16,
        reasoning={"effort": effort},
    )
    assert isinstance(response.output_text, str)

@pytest.mark.live
def test_openai_o3_rejects_too_low_max_output_tokens_live() -> None:
    _skip_if_live_disabled()
    try:
        create_response(
            system_prompt="System.",
            user_prompt="User.",
            model="o3-2025-04-16",
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


@pytest.mark.live
def test_openai_o3_rejects_invalid_reasoning_effort_live() -> None:
    _skip_if_live_disabled()
    try:
        create_response(
            system_prompt="System.",
            user_prompt="User.",
            model="o3-2025-04-16",
            max_output_tokens=16,
            reasoning={"effort": "ultra"},
        )
    except RuntimeError as exc:
        message = str(exc)
        if "server_error" in message or "Internal Server Error" in message:
            pytest.skip("OpenAI server error; retry live test.")
        if "unsupported" not in message and "invalid" not in message:
            raise
    else:
        raise AssertionError("Expected invalid reasoning effort to be rejected.")
