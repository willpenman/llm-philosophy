"""Live Grok API tests.

Marked as live because they incur cost and require API access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.providers.grok import create_chat_completion  # noqa: E402

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
    if os.getenv("RUN_LIVE_GROK") != "1":
        pytest.skip("Set RUN_LIVE_GROK=1 to enable live Grok tests.")
    if not os.getenv("XAI_API_KEY"):
        pytest.skip("Missing XAI_API_KEY for live Grok tests.")


def _create_completion_or_skip_on_server_error(request: pytest.FixtureRequest, **kwargs):
    try:
        return create_chat_completion(**kwargs)
    except RuntimeError as exc:
        message = str(exc)
        if "server_error" in message or "Internal Server Error" in message:
            pytest.skip(
                f"Grok server error in {request.node.nodeid}; retry live test."
            )
        raise


@pytest.mark.live
@pytest.mark.parametrize("model", ["grok-4-1-fast-reasoning"])
def test_grok_accepts_system_prompt_live(
    request: pytest.FixtureRequest, model: str
) -> None:
    _skip_if_live_disabled()
    response = _create_completion_or_skip_on_server_error(
        request=request,
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=16,
        stream=False,
    ) 
    assert "OK" in response.output_text.upper()


@pytest.mark.live
@pytest.mark.parametrize("model", ["grok-3", "grok-4-1-fast-reasoning"])
def test_grok_accepts_temperature_live(
    request: pytest.FixtureRequest, model: str
) -> None:
    _skip_if_live_disabled()
    response = _create_completion_or_skip_on_server_error(
        request=request,
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=16,
        temperature=0.2,
        stream=False,
    )
    assert "OK" in response.output_text.upper()

