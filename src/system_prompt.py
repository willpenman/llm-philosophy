"""Loader for the shared system prompt fixture."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import ModuleType
from typing import Any


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


def _default_max_output_tokens(model: str | None) -> int | None:
    if not model:
        return None
    # Local imports to avoid provider dependencies at import time.
    from src.providers import anthropic, fireworks, gemini, grok, openai

    if model in anthropic.MODEL_DEFAULTS:
        return anthropic.MODEL_DEFAULTS[model].get("max_output_tokens")
    if model in openai.MODEL_DEFAULTS:
        return openai.MODEL_DEFAULTS[model].get("max_output_tokens")
    if model in gemini.MODEL_DEFAULTS:
        return gemini.MODEL_DEFAULTS[model].get("max_output_tokens")
    if model in grok.MODEL_DEFAULTS:
        return grok.MODEL_DEFAULTS[model].get("max_output_tokens")

    model_id = fireworks.resolve_model(model)
    if model_id in fireworks.MODEL_DEFAULTS:
        return fireworks.MODEL_DEFAULTS[model_id].get("max_output_tokens")
    return None


def _length_guidance_sentence(
    module: ModuleType, max_output_tokens: int | None
) -> str | None:
    if max_output_tokens is None:
        return None
    table = getattr(module, "OUTPUT_LENGTH_GUIDANCE", None)
    if not isinstance(table, list) or not table:
        return None
    template = getattr(module, "OUTPUT_LENGTH_SENTENCE_TEMPLATE", None)
    if not isinstance(template, str) or not template.strip():
        return None
    selected: dict[str, Any] | None = None
    for entry in table:
        if not isinstance(entry, dict):
            continue
        limit = entry.get("max_output_tokens")
        label = entry.get("label")
        if not isinstance(limit, int) or not isinstance(label, str):
            continue
        if max_output_tokens <= limit:
            selected = entry
            break
        selected = entry
    if not selected:
        return None
    label = selected.get("label")
    if not isinstance(label, str) or not label.strip():
        return None
    return template.format(label=label, max_output_tokens=max_output_tokens)


def load_system_prompt(
    system_path: Path | None = None,
    *,
    model: str | None = None,
    max_output_tokens: int | None = None,
) -> SystemPrompt:
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
    resolved_max_output_tokens = max_output_tokens or _default_max_output_tokens(model)
    length_sentence = _length_guidance_sentence(module, resolved_max_output_tokens)
    if length_sentence:
        text = f"{text.strip()}{length_sentence}"

    return SystemPrompt(
        name=name if isinstance(name, str) else None,
        version=version if isinstance(version, str) else None,
        text=text,
        metadata=metadata,
        path=path,
    )
