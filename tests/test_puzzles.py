"""Smoke tests for puzzle fixtures."""

from __future__ import annotations

from src.puzzles import list_puzzle_names, load_puzzle  # noqa: E402


def test_list_puzzle_names_includes_panopticon() -> None:
    puzzle_dir = ROOT / "prompts" / "puzzles"
    names = list_puzzle_names(puzzle_dir)
    assert "panopticon" in names


def test_load_puzzle_smoke() -> None:
    puzzle_dir = ROOT / "prompts" / "puzzles"
    puzzle = load_puzzle("panopticon", puzzle_dir)
    assert puzzle.name == "panopticon"
    assert puzzle.text.strip()
