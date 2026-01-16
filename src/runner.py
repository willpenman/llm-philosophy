"""Evaluation runner for provider adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from providers.openai import (
    build_response_request,
    display_model_name,
    display_provider_name,
    extract_output_text,
    inject_reasoning_summary_from_stream,
    price_schedule_for_model,
    require_api_key,
    send_response_request,
    supports_reasoning,
)
from providers.gemini import (
    build_generate_content_request,
    display_model_name as display_gemini_model_name,
    display_provider_name as display_gemini_provider_name,
    price_schedule_for_model as gemini_price_schedule_for_model,
    require_api_key as require_gemini_api_key,
    send_generate_content_request,
    supports_reasoning as gemini_supports_reasoning,
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
    request_path: Path | None
    response_text_path: Path | None
    sse_event_path: Path | None


def _format_timestamp(created_at: str) -> str:
    timestamp = datetime.fromisoformat(created_at)
    timestamp = timestamp.astimezone(timezone.utc)
    return timestamp.strftime("%Y-%m-%dT%H%M%SZ")


def _build_progress_callback(
    max_tokens: int | None,
    *,
    suffix: str,
) -> Callable[[int], None]:
    progress_width = len(str(max_tokens)) if isinstance(max_tokens, int) else 0
    last_progress = {"chars": 0}

    def _progress(chars: int) -> None:
        if progress_width <= 0:
            return
        if chars == last_progress["chars"]:
            return
        last_progress["chars"] = chars
        # during streaming, we only have the characters themselves
        # use "1 token per 4 characters" standard estimate
        capped = str(int(chars / 4)).zfill(progress_width)
        total = str(max_tokens).zfill(progress_width)
        print(
            f"\rReceiving output text, ≈ {capped} / {total} {suffix}",
            end="",
            flush=True,
        )

    return _progress


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
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    reasoning: dict[str, Any] | None = None,
    seed: int | None = None,
    stream: bool = True,
    special_settings: str | None = None,
    dry_run: bool = False,
    debug_sse: bool = False,
    debug_sse_path: Path | None = None,
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
    if reasoning is None and supports_reasoning(model):
        reasoning = {"effort": "high", "summary": "detailed"}

    if debug_sse and not stream:
        raise ValueError("debug_sse requires stream=True")

    request_payload = build_response_request(
        system_prompt=system_prompt.text,
        user_prompt=puzzle.text,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        reasoning=reasoning,
        seed=seed,
        stream=stream,
    )

    store: ResponseStore | None = None
    request_path: Path | None = None
    if not debug_sse:
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
            sse_event_path=None,
        )

    request_started_at = created_at
    print(
        f"requesting puzzle={puzzle.name} model={model}",
        flush=True,
    )
    max_tokens = request_payload.get("max_output_tokens")
    if stream and max_tokens is None:
        print("Set max tokens to see streaming info.", flush=True)
    progress_callback = _build_progress_callback(max_tokens, suffix="tokens")

    streamed_chunks: list[str] = []

    def _collect_delta(delta: str) -> None:
        streamed_chunks.append(delta)

    sse_event_path = None
    if debug_sse:
        base_dir = _repo_root() / "tmp"
        timestamp = _format_timestamp(created_at)
        sse_event_path = (
            base_dir / f"openai-sse-{model}-{run_id}-{timestamp}.jsonl"
        )
        print(f"DEBUG MODE: skips responses; writing SSE events to {sse_event_path}")

    stream_capture: dict[str, Any] | None = {} if stream else None
    response_payload = send_response_request(
        request_payload,
        api_key=api_key or require_api_key(),
        progress_callback=progress_callback if stream else None,
        stream_text_callback=_collect_delta if stream else None,
        sse_event_path=sse_event_path,
        stream_capture=stream_capture,
    )
    inject_reasoning_summary_from_stream(response_payload, stream_capture)
    if stream and isinstance(max_tokens, int):
        print("", flush=True)
    request_completed_at = utc_now_iso()
    output_text = extract_output_text(response_payload)
    if stream and streamed_chunks and not output_text:
        output_text = "".join(streamed_chunks)
    usage = response_payload.get("usage") if isinstance(response_payload, dict) else None
    if isinstance(usage, dict):
        output_tokens = usage.get("output_tokens")
        thinking_tokens = None
        details = usage.get("output_tokens_details")
        if isinstance(details, dict):
            thinking_tokens = details.get("reasoning_tokens")
        if isinstance(output_tokens, int) or isinstance(thinking_tokens, int) or thinking_tokens is None:
            if isinstance(thinking_tokens, int):
                thinking_label = str(thinking_tokens)
            elif thinking_tokens is None:
                thinking_label = "0 (disabled)"
            else:
                thinking_label = "unknown"
            output_label = (
                str(output_tokens) if isinstance(output_tokens, int) else "unknown"
            )
            print(
                f"Actual tokens: thinking={thinking_label}, output={output_label}",
                flush=True,
            )
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
    derived["model_alias"] = display_model_name(model)
    stored_text = None
    if store is not None:
        stored_text = store.record_response(
            run_id=run_id,
            created_at=created_at,
            provider=provider,
            model=model,
            model_alias=display_model_name(model),
            provider_alias=display_provider_name(provider),
            puzzle_name=puzzle.name,
            puzzle_title_prefix="Philosophy problem",
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
        response_text_path=stored_text.path if stored_text else None,
        sse_event_path=sse_event_path,
    )


def run_gemini_puzzle(
    *,
    puzzle_name: str,
    model: str = "gemini-2.0-flash-lite-001",
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    thinking_config: dict[str, Any] | None = None,
    stream: bool = True,
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
    provider = "gemini"
    special_settings_label = normalize_special_settings(special_settings)

    if thinking_config is None and gemini_supports_reasoning(model):
        thinking_config = {"thinking_level": "HIGH", "include_thoughts": True}

    request_payload = build_generate_content_request(
        system_prompt=system_prompt.text,
        user_prompt=puzzle.text,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        thinking_config=thinking_config,
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
            sse_event_path=None,
        )

    request_started_at = created_at
    print(
        f"requesting puzzle={puzzle.name} model={model}",
        flush=True,
    )
    max_tokens = None
    config = request_payload.get("config")
    if isinstance(config, dict):
        max_tokens = config.get("max_output_tokens")
    progress_callback = _build_progress_callback(
        max_tokens,
        suffix="total possible",
    )

    streamed_chars = {"total": 0}

    def _collect_delta(delta: str) -> None:
        streamed_chars["total"] += len(delta)
        progress_callback(streamed_chars["total"])

    response = send_generate_content_request(
        request_payload,
        api_key=api_key or require_gemini_api_key(),
        stream=stream,
        stream_text_callback=_collect_delta if stream else None,
    )
    if stream and isinstance(max_tokens, int):
        print("", flush=True)
    request_completed_at = utc_now_iso()
    output_text = response.output_text
    usage = response.payload.get("usage_metadata") if isinstance(response.payload, dict) else None
    if isinstance(usage, dict):
        output_tokens = usage.get("candidates_token_count")
        thinking_tokens = usage.get("thoughts_token_count")
        if isinstance(output_tokens, int) or isinstance(thinking_tokens, int) or thinking_tokens is None:
            if isinstance(thinking_tokens, int):
                thinking_label = str(thinking_tokens)
            elif thinking_tokens is None:
                thinking_label = "0 (disabled)"
            else:
                thinking_label = "unknown"
            output_label = (
                str(output_tokens) if isinstance(output_tokens, int) else "unknown"
            )
            print(
                f"Actual tokens: thinking={thinking_label}, output={output_label}",
                flush=True,
            )
    input_text = format_input_text(system_prompt.text, puzzle.text)
    derived: dict[str, Any] = {
        "timing": {
            "request_started_at": request_started_at,
            "request_completed_at": request_completed_at,
        }
    }
    price_schedule = gemini_price_schedule_for_model(model)
    if price_schedule is not None:
        derived["price_schedule"] = price_schedule
    derived["model_alias"] = display_gemini_model_name(model)
    stored_text = store.record_response(
        run_id=run_id,
        created_at=created_at,
        provider=provider,
        model=model,
        model_alias=display_gemini_model_name(model),
        provider_alias=display_gemini_provider_name(provider),
        puzzle_name=puzzle.name,
        puzzle_title_prefix="Philosophy problem",
        puzzle_version=puzzle.version,
        puzzle_title=puzzle.title,
        special_settings=special_settings_label,
        request_payload=request_payload,
        response_payload=response.payload,
        input_text=input_text,
        output_text=output_text,
        derived=derived,
    )
    return RunResult(
        run_id=run_id,
        request_payload=request_payload,
        response_payload=response.payload,
        output_text=output_text,
        request_path=request_path,
        response_text_path=stored_text.path,
        sse_event_path=None,
    )
