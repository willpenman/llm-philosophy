"""Puzzle loader for prompt fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import ModuleType
from typing import Iterable


@dataclass(frozen=True)
class Puzzle:
    name: str
    title: str | None
    version: str | None
    text: str
    metadata: dict
    path: Path


def _default_puzzle_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "prompts" / "puzzles"


def _load_module(path: Path) -> ModuleType:
    loader = SourceFileLoader(path.stem, str(path))
    spec = spec_from_loader(path.stem, loader)
    if spec is None:
        raise ImportError(f"Unable to load puzzle module: {path}")
    module = module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"Unable to load puzzle module: {path}")
    spec.loader.exec_module(module)
    return module


def _coerce_metadata(value: object) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    raise TypeError("PUZZLE_METADATA must be a dict if provided")


def _build_puzzle(module: ModuleType, path: Path) -> Puzzle:
    if not hasattr(module, "PUZZLE_TEXT"):
        raise ValueError(f"Missing PUZZLE_TEXT in {path.name}")
    text = getattr(module, "PUZZLE_TEXT")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"PUZZLE_TEXT must be a non-empty string in {path.name}")

    name = getattr(module, "PUZZLE_NAME", path.stem)
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"PUZZLE_NAME must be a non-empty string in {path.name}")

    title = getattr(module, "PUZZLE_TITLE", None)
    if title is not None and not isinstance(title, str):
        raise ValueError(f"PUZZLE_TITLE must be a string in {path.name}")

    version = getattr(module, "PUZZLE_VERSION", None)
    if version is not None and not isinstance(version, str):
        raise ValueError(f"PUZZLE_VERSION must be a string in {path.name}")

    metadata = _coerce_metadata(getattr(module, "PUZZLE_METADATA", None))

    return Puzzle(
        name=name,
        title=title,
        version=version,
        text=text,
        metadata=metadata,
        path=path,
    )


def list_puzzle_paths(puzzle_dir: Path | None = None) -> list[Path]:
    root = puzzle_dir or _default_puzzle_dir()
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix == ".py" and not path.name.startswith("__")
    )


def list_puzzle_names(puzzle_dir: Path | None = None) -> list[str]:
    return [path.stem for path in list_puzzle_paths(puzzle_dir)]


def load_puzzle(name: str, puzzle_dir: Path | None = None) -> Puzzle:
    root = puzzle_dir or _default_puzzle_dir()
    path = root / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(f"Puzzle not found: {name}")
    module = _load_module(path)
    puzzle = _build_puzzle(module, path)
    if puzzle.name != name:
        raise ValueError(
            f"Puzzle name mismatch for {name}: module defines {puzzle.name!r}"
        )
    return puzzle


def load_all_puzzles(puzzle_dir: Path | None = None) -> Iterable[Puzzle]:
    for path in list_puzzle_paths(puzzle_dir):
        module = _load_module(path)
        yield _build_puzzle(module, path)
