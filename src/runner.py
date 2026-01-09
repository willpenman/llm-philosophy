"""Evaluation runner for provider adapters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from providers.openai import (
    build_response_request,
    extract_output_text,
    price_schedule_for_model,
    require_api_key,
    send_response_request,
)
from src.puzzles import Puzzle, load_puzzle
from src.storage import ResponseStore, format_input_text, normalize_special_settings, utc_now_iso
from src.system_prompt import SystemPrompt, load_system_prompt


@dataclass(frozen=True)
class RunResult:
    run_id: str
    request_payload: dict[str, Any]
    response_payload: dict[str, Any] | None
    output_text: str
    request_path: Path
    response_text_path: Path | None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_responses_dir() -> Path:
    return _repo_root() / "responses"


def _load_fixtures(
    puzzle_name: str, puzzle_dir: Path | None, system_path: Path | None
) -> tuple[SystemPrompt, Puzzle]:
    system_prompt = load_system_prompt(system_path)
    puzzle = load_puzzle(puzzle_name, puzzle_dir)
    return system_prompt, puzzle


def run_openai_puzzle(
    *,
    puzzle_name: str,
    model: str = "o3-2025-04-16",
    max_output_tokens: int | None,
    temperature: float | None = None,
    reasoning: dict[str, Any] | None = None,
    seed: int | None = None,
    special_settings: str | None = None,
    dry_run: bool = False,
    run_id: str | None = None,
    puzzle_dir: Path | None = None,
    system_path: Path | None = None,
    responses_dir: Path | None = None,
    api_key: str | None = None,
) -> RunResult:
    system_prompt, puzzle = _load_fixtures(puzzle_name, puzzle_dir, system_path)
    created_at = utc_now_iso()
    run_id = run_id or uuid4().hex
    provider = "openai"
    special_settings_label = normalize_special_settings(special_settings)
    reasoning = reasoning or {"effort": "high"}

    request_payload = build_response_request(
        system_prompt=system_prompt.text,
        user_prompt=puzzle.text,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        reasoning=reasoning,
        seed=seed,
    )

    store = ResponseStore(responses_dir or _default_responses_dir())
    request_path = store.record_request(
        run_id=run_id,
        created_at=created_at,
        provider=provider,
        model=model,
        puzzle_name=puzzle.name,
        puzzle_version=puzzle.version,
        special_settings=special_settings_label,
        request_payload=request_payload,
    )

    if dry_run:
        return RunResult(
            run_id=run_id,
            request_payload=request_payload,
            response_payload=None,
            output_text="",
            request_path=request_path,
            response_text_path=None,
        )

    request_started_at = created_at
    response_payload = send_response_request(
        request_payload, api_key=api_key or require_api_key()
    )
    request_completed_at = utc_now_iso()
    output_text = extract_output_text(response_payload)
    input_text = format_input_text(system_prompt.text, puzzle.text)
    derived: dict[str, Any] = {
        "timing": {
            "request_started_at": request_started_at,
            "request_completed_at": request_completed_at,
        }
    }
    price_schedule = price_schedule_for_model(model)
    if price_schedule is not None:
        derived["price_schedule"] = price_schedule
    stored_text = store.record_response(
        run_id=run_id,
        created_at=created_at,
        provider=provider,
        model=model,
        puzzle_name=puzzle.name,
        puzzle_version=puzzle.version,
        puzzle_title=puzzle.title,
        special_settings=special_settings_label,
        request_payload=request_payload,
        response_payload=response_payload,
        input_text=input_text,
        output_text=output_text,
        derived=derived,
    )
    return RunResult(
        run_id=run_id,
        request_payload=request_payload,
        response_payload=response_payload,
        output_text=output_text,
        request_path=request_path,
        response_text_path=stored_text.path,
    )
