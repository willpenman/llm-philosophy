"""Shared helpers for reading and extracting data from stored responses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.providers import anthropic, fireworks, gemini, grok, openai


def extract_text_from_blocks(blocks: Any) -> str:
    """Extract plain text from provider content blocks."""
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


def extract_input_text(provider: str, request_payload: dict[str, Any]) -> tuple[str, str]:
    """Extract system and user text from a request payload.

    Returns (system_text, user_text) tuple.
    """
    if provider == "anthropic":
        system_blocks = request_payload.get("system", [])
        system_text = extract_text_from_blocks(system_blocks)
        messages = request_payload.get("messages", [])
        user_text = ""
        if isinstance(messages, list):
            for message in messages:
                if isinstance(message, dict) and message.get("role") == "user":
                    user_text = extract_text_from_blocks(message.get("content"))
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
                    system_text = extract_text_from_blocks(content)
                elif role == "user":
                    user_text = extract_text_from_blocks(content)
        return system_text, user_text
    if provider == "gemini":
        config = request_payload.get("config", {})
        system_text = ""
        if isinstance(config, dict):
            system_text = extract_text_from_blocks(config.get("system_instruction"))
        user_text = extract_text_from_blocks(request_payload.get("contents"))
        return system_text, user_text
    if provider in {"fireworks", "deepseek", "kimi", "qwen", "meta"}:
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
                    system_text = extract_text_from_blocks(content)
                elif role == "user":
                    user_text = extract_text_from_blocks(content)
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
                    system_text = extract_text_from_blocks(content)
                elif role == "user":
                    user_text = extract_text_from_blocks(content)
        return system_text, user_text
    return "", ""


def extract_output_text(provider: str, response_payload: dict[str, Any]) -> str:
    """Extract output text from a response payload."""
    if provider == "anthropic":
        return anthropic.extract_output_text(response_payload)
    if provider == "openai":
        return openai.extract_output_text(response_payload)
    if provider == "gemini":
        return gemini.extract_output_text(response_payload)
    if provider in {"fireworks", "deepseek", "kimi", "qwen", "meta"}:
        return fireworks.extract_output_text(response_payload)
    if provider == "grok":
        return grok.extract_output_text(response_payload)
    return ""


def display_names(provider: str, model: str) -> tuple[str, str]:
    """Get human-readable display names for model and provider.

    Returns (model_display, provider_display) tuple.
    """
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
    if provider in {"fireworks", "deepseek", "kimi", "qwen", "meta"}:
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


def release_date(provider: str, model: str) -> str | None:
    """Get the release date for a model in YYYY-MM-DD format.

    Returns None if the release date is not known.
    """
    if provider == "anthropic":
        return anthropic.MODEL_RELEASE_DATES.get(model)
    if provider == "openai":
        return openai.MODEL_RELEASE_DATES.get(model)
    if provider == "gemini":
        return gemini.MODEL_RELEASE_DATES.get(model)
    if provider in {"fireworks", "deepseek", "kimi", "qwen", "meta"}:
        return fireworks.MODEL_RELEASE_DATES.get(model)
    if provider == "grok":
        return grok.MODEL_RELEASE_DATES.get(model)
    return None


def find_response(
    responses_dir: Path,
    model: str,
    puzzle_name: str,
) -> dict[str, Any] | None:
    """Find the most recent response for a given model and puzzle.

    Searches all provider directories for matching responses.
    Returns the full JSONL record or None if not found.
    """
    matches: list[tuple[str, dict[str, Any]]] = []

    for response_path in responses_dir.glob("*/*/responses.jsonl"):
        with response_path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                record_model = record.get("model")
                record_puzzle = record.get("puzzle_name")
                if record_model == model and record_puzzle == puzzle_name:
                    created_at = record.get("created_at", "")
                    matches.append((created_at, record))

    if not matches:
        return None

    # Return most recent by created_at
    matches.sort(key=lambda x: x[0], reverse=True)
    return matches[0][1]


def format_response_plaintext(
    *,
    puzzle_prefix: str,
    display_name: str,
    puzzle_version: str | None,
    model_display: str,
    provider_display: str,
    settings_display: str,
    display_date: str,
    input_text: str,
    output_text: str,
) -> str:
    """Format a response as plaintext for display or LLM consumption."""
    version_suffix = f" (v{puzzle_version})" if puzzle_version else ""

    lines = [
        f"{puzzle_prefix}: {display_name}{version_suffix}",
        f"Model: {model_display} ({provider_display}){settings_display}",
        f"Completed: {display_date}",
        "",
        "---- INPUT ----",
        input_text,
        "",
        f"---- {model_display}'S OUTPUT ----",
        output_text,
    ]
    return "\n".join(lines)
