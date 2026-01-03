"""Loader for the shared system prompt fixture."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import ModuleType


@dataclass(frozen=True)
class SystemPrompt:
    name: str | None
    version: str | None
    text: str
    metadata: dict
    path: Path


def _default_system_path() -> Path:
    return Path(__file__).resolve().parents[1] / "prompts" / "system.py"


def _load_module(path: Path) -> ModuleType:
    loader = SourceFileLoader(path.stem, str(path))
    spec = spec_from_loader(path.stem, loader)
    if spec is None:
        raise ImportError(f"Unable to load system prompt module: {path}")
    module = module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"Unable to load system prompt module: {path}")
    spec.loader.exec_module(module)
    return module


def _coerce_metadata(value: object) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    raise TypeError("PROMPT_METADATA must be a dict if provided")


def load_system_prompt(system_path: Path | None = None) -> SystemPrompt:
    path = system_path or _default_system_path()
    if not path.exists():
        raise FileNotFoundError(f"System prompt not found: {path}")
    module = _load_module(path)
    if not hasattr(module, "SYSTEM_PROMPT"):
        raise ValueError(f"Missing SYSTEM_PROMPT in {path.name}")
    text = getattr(module, "SYSTEM_PROMPT")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"SYSTEM_PROMPT must be a non-empty string in {path.name}")

    metadata = _coerce_metadata(getattr(module, "PROMPT_METADATA", None))
    name = metadata.get("name") if isinstance(metadata, dict) else None
    version = metadata.get("version") if isinstance(metadata, dict) else None

    return SystemPrompt(
        name=name if isinstance(name, str) else None,
        version=version if isinstance(version, str) else None,
        text=text,
        metadata=metadata,
        path=path,
    )
