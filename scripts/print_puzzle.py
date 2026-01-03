"""Print the system prompt and a puzzle for quick inspection."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.puzzles import load_puzzle  # noqa: E402


def _load_system_prompt() -> str:
    prompt_path = ROOT / "prompts" / "system.py"
    namespace: dict[str, object] = {}
    exec(prompt_path.read_text(encoding="utf-8"), namespace)
    prompt = namespace.get("SYSTEM_PROMPT")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("SYSTEM_PROMPT must be a non-empty string")
    return prompt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print the system prompt and a puzzle fixture."
    )
    parser.add_argument("name", help="Puzzle name (filename without .py)")
    args = parser.parse_args()

    puzzle_dir = ROOT / "prompts" / "puzzles"
    puzzle = load_puzzle(args.name, puzzle_dir)
    system_prompt = _load_system_prompt()

    print("System:\n")
    print(system_prompt)
    print("\nUser:\n")
    print(puzzle.text)


if __name__ == "__main__":
    main()
