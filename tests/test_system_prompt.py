"""Smoke tests for the system prompt fixture."""

from __future__ import annotations

from pathlib import Path

from src.system_prompt import load_system_prompt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_load_system_prompt_smoke() -> None:
    system_prompt = load_system_prompt(ROOT / "prompts" / "system.py")
    assert system_prompt.text.strip()
