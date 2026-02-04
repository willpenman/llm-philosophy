"""Live Fireworks API tests.

Marked as live because they incur cost and require API access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.providers.fireworks import create_chat_completion  # noqa: E402

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
@pytest.mark.parametrize(
    "model",
    [
        "deepseek-v3p2",
        "deepseek-v3-0324",
        "qwen3-vl-235b-thinking",
        "qwen2p5-vl-32b",
        "kimi-k2p5",
        "kimi-k2-instruct-0905",
        "llama-v3p3-70b-instruct",
    ],
)
def test_fireworks_accepts_system_prompt_live(model: str) -> None:
    _skip_if_live_disabled()
    response = create_chat_completion(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=16,
    )
    assert "OK" in response.output_text.upper()


@pytest.mark.live
@pytest.mark.parametrize(
    "model",
    [
        "deepseek-v3p2",
        "deepseek-v3-0324",
        "qwen3-vl-235b-thinking",
        "qwen2p5-vl-32b",
        "kimi-k2p5",
        "kimi-k2-instruct-0905",
        "llama-v3p3-70b-instruct",
    ],
)
def test_fireworks_streaming_captures_output_live(model: str) -> None:
    _skip_if_live_disabled()
    response = create_chat_completion(
        system_prompt="You are a test harness. Follow the user's instructions.",
        user_prompt=(
            "Write a short paragraph about model introspection. "
            "End with the word END."
        ),
        model=model,
        max_output_tokens=1012,
        stream=True,
    )
    normalized = response.output_text.strip().rstrip(".!?")
    assert normalized.endswith("END")


@pytest.mark.live
@pytest.mark.parametrize(
    ("model", "accepts_reasoning_effort"),
    [
        ("deepseek-v3p2", True),
        ("deepseek-v3-0324", True),
        ("qwen3-vl-235b-thinking", True),
        ("qwen2p5-vl-32b", False),
        ("kimi-k2p5", True),
        ("kimi-k2-instruct-0905", True),
        ("llama-v3p3-70b-instruct", False),
    ],
)
def test_fireworks_reasoning_effort_acceptance_live(
    model: str, accepts_reasoning_effort: bool
) -> None:
    _skip_if_live_disabled()
    if accepts_reasoning_effort:
        response = create_chat_completion(
            system_prompt="You are a test harness. Reply with OK.",
            user_prompt="Reply with OK.",
            model=model,
            max_output_tokens=512,
            reasoning_effort="high",
        )
        assert "OK" in response.output_text.upper()
    else:
        with pytest.raises(RuntimeError):
            create_chat_completion(
                system_prompt="You are a test harness. Reply with OK.",
                user_prompt="Reply with OK.",
                model=model,
                max_output_tokens=512,
                reasoning_effort="high",
            )


@pytest.mark.live
@pytest.mark.parametrize(
    "model",
    [
        "deepseek-v3p2",
        "deepseek-v3-0324",
        "qwen3-vl-235b-thinking",
        "qwen2p5-vl-32b",
        "kimi-k2p5",
        "kimi-k2-instruct-0905",
        "llama-v3p3-70b-instruct",
    ],
)
def test_fireworks_temperature_acceptance_live(model: str) -> None:
    _skip_if_live_disabled()
    response = create_chat_completion(
        system_prompt="You are a test harness. Reply with OK.",
        user_prompt="Reply with OK.",
        model=model,
        max_output_tokens=32,
        temperature=0.2,
    )
    assert "OK" in response.output_text.upper()
