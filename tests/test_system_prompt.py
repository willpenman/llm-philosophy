"""Smoke tests for the system prompt fixture."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.system_prompt import load_system_prompt  # noqa: E402


def test_load_system_prompt_smoke() -> None:
    system_prompt = load_system_prompt(ROOT / "prompts" / "system.py")
    assert system_prompt.text.strip()
