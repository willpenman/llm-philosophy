"""Print the system prompt and a puzzle for quick inspection."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.puzzles import load_puzzle
from src.system_prompt import load_system_prompt

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print the system prompt and a puzzle fixture."
    )
    parser.add_argument("name", help="Puzzle name (filename without .py)")
    parser.add_argument(
        "--model",
        help="Model name used to append output-length guidance to the system prompt.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        help="Override the model max output token limit for length guidance.",
    )
    args = parser.parse_args()

    puzzle_dir = ROOT / "prompts" / "puzzles"
    puzzle = load_puzzle(args.name, puzzle_dir)
    system_prompt = load_system_prompt(
        ROOT / "prompts" / "system.py",
        model=args.model,
        max_output_tokens=args.max_output_tokens,
    ).text

    print("System:\n")
    print(system_prompt)
    print("\nUser:\n")
    print(puzzle.text)


if __name__ == "__main__":
    main()
