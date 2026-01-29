"""Backfill .docx response files from existing response records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.puzzles import load_puzzle
from src.storage import (
    _format_display_date,
    _format_filename_timestamp,
    normalize_special_settings,
    write_response_docx,
)
from src.providers import anthropic, fireworks, gemini, grok, openai

ROOT = Path(__file__).resolve().parents[1]


def _extract_text_from_blocks(blocks: Any) -> str:
    if isinstance(blocks, str):
        return blocks
    if isinstance(blocks, list):
        parts: list[str] = []
        for item in blocks:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n\n".join(parts)
    return ""


def _extract_input_text(provider: str, request_payload: dict[str, Any]) -> tuple[str, str]:
    if provider == "anthropic":
        system_blocks = request_payload.get("system", [])
        system_text = _extract_text_from_blocks(system_blocks)
        messages = request_payload.get("messages", [])
        user_text = ""
        if isinstance(messages, list):
            for message in messages:
                if isinstance(message, dict) and message.get("role") == "user":
                    user_text = _extract_text_from_blocks(message.get("content"))
                    break
        return system_text, user_text
    if provider == "openai":
        system_text = ""
        user_text = ""
        items = request_payload.get("input", [])
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                role = item.get("role")
                content = item.get("content")
                if role == "system":
                    system_text = _extract_text_from_blocks(content)
                elif role == "user":
                    user_text = _extract_text_from_blocks(content)
        return system_text, user_text
    if provider == "gemini":
        config = request_payload.get("config", {})
        system_text = ""
        if isinstance(config, dict):
            system_text = _extract_text_from_blocks(config.get("system_instruction"))
        user_text = _extract_text_from_blocks(request_payload.get("contents"))
        return system_text, user_text
    if provider in {"fireworks", "deepseek"}:
        messages = request_payload.get("messages", [])
        system_text = ""
        user_text = ""
        if isinstance(messages, list):
            for message in messages:
                if not isinstance(message, dict):
                    continue
                role = message.get("role")
                content = message.get("content")
                if role == "system":
                    system_text = _extract_text_from_blocks(content)
                elif role == "user":
                    user_text = _extract_text_from_blocks(content)
        return system_text, user_text
    if provider == "grok":
        messages = request_payload.get("messages", [])
        system_text = ""
        user_text = ""
        if isinstance(messages, list):
            for message in messages:
                if not isinstance(message, dict):
                    continue
                role = message.get("role")
                content = message.get("content")
                if role == "system":
                    system_text = _extract_text_from_blocks(content)
                elif role == "user":
                    user_text = _extract_text_from_blocks(content)
        return system_text, user_text
    return "", ""


def _display_names(provider: str, model: str) -> tuple[str, str]:
    if provider == "anthropic":
        return (
            anthropic.display_model_name(model),
            anthropic.display_provider_name(provider),
        )
    if provider == "openai":
        return (
            openai.display_model_name(model),
            openai.display_provider_name(provider),
        )
    if provider == "gemini":
        return (
            gemini.display_model_name(model),
            gemini.display_provider_name(provider),
        )
    if provider in {"fireworks", "deepseek"}:
        return (
            fireworks.display_model_name(model),
            fireworks.display_provider_name(provider),
        )
    if provider == "grok":
        return (
            grok.display_model_name(model),
            grok.display_provider_name(provider),
        )
    return model, provider


def _extract_output_text(provider: str, response_payload: dict[str, Any]) -> str:
    if provider == "anthropic":
        return anthropic.extract_output_text(response_payload)
    if provider == "openai":
        return openai.extract_output_text(response_payload)
    if provider == "gemini":
        return gemini.extract_output_text(response_payload)
    if provider in {"fireworks", "deepseek"}:
        return fireworks.extract_output_text(response_payload)
    if provider == "grok":
        return grok.extract_output_text(response_payload)
    return ""


def _docx_path(
    base_dir: Path,
    provider: str,
    model: str,
    special_settings: str,
    puzzle_name: str,
    puzzle_version: str | None,
    created_at: str,
) -> Path:
    version = puzzle_version or "unknown"
    timestamp = _format_filename_timestamp(created_at)
    filename = f"{special_settings}-{puzzle_name}-v{version}-{timestamp}.docx"
    return base_dir / provider / model / "texts" / filename


def backfill_from_jsonl(root: Path) -> int:
    count = 0
    for response_path in root.rglob("responses/*/*/responses.jsonl"):
        with response_path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                provider = record.get("provider")
                model = record.get("model")
                puzzle_name = record.get("puzzle_name")
                puzzle_version = record.get("puzzle_version")
                created_at = record.get("created_at")
                special_settings = normalize_special_settings(
                    record.get("special_settings")
                )
                request_payload = record.get("request", {})
                response_payload = record.get("response", {})
                if not isinstance(provider, str) or not isinstance(model, str):
                    continue
                if not isinstance(puzzle_name, str) or not isinstance(created_at, str):
                    continue
                if not isinstance(request_payload, dict) or not isinstance(
                    response_payload, dict
                ):
                    continue

                system_text, user_text = _extract_input_text(provider, request_payload)
                input_text = f"System:\n{system_text}\n\nUser:\n{user_text}"
                output_text = _extract_output_text(provider, response_payload)

                model_display, provider_display = _display_names(provider, model)
                settings_display = (
                    ""
                    if normalize_special_settings(special_settings) == "default"
                    else f", {special_settings}"
                )
                puzzle = load_puzzle(puzzle_name, ROOT / "prompts" / "puzzles")
                display_name = puzzle.title or puzzle_name
                puzzle_prefix = "Philosophy problem"
                display_date = _format_display_date(created_at)
                docx_path = _docx_path(
                    root / "responses",
                    provider,
                    model,
                    special_settings,
                    puzzle_name,
                    puzzle_version,
                    created_at,
                )
                docx_path.parent.mkdir(parents=True, exist_ok=True)
                write_response_docx(
                    path=docx_path,
                    puzzle_prefix=puzzle_prefix,
                    display_name=display_name,
                    puzzle_version=puzzle_version if isinstance(puzzle_version, str) else None,
                    model_display=model_display,
                    provider_display=provider_display,
                    settings_display=settings_display,
                    display_date=display_date,
                    input_text=input_text,
                    output_text=output_text,
                )
                count += 1
    return count


def main() -> None:
    total = backfill_from_jsonl(ROOT)
    print(f"Created {total} .docx files.")


if __name__ == "__main__":
    main()
