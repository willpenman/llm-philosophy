"""List available puzzle fixtures."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from src.puzzles import list_puzzle_names  # noqa: E402


def main() -> None:
    puzzle_dir = ROOT / "prompts" / "puzzles"
    for name in list_puzzle_names(puzzle_dir):
        print(name)


if __name__ == "__main__":
    main()
