"""Evaluation runner for provider adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from src.providers.openai import (
    build_response_request,
    calculate_cost_breakdown as openai_calculate_cost_breakdown,
    display_model_name,
    display_provider_name,
    extract_usage_breakdown as openai_extract_usage_breakdown,
    extract_output_text,
    extract_reasoning_summary_from_stream,
    price_schedule_for_model,
    require_api_key,
    send_response_request,
    supports_reasoning,
)
from src.providers.gemini import (
    build_generate_content_request,
    calculate_cost_breakdown as gemini_calculate_cost_breakdown,
    default_temperature_for_model as gemini_default_temperature_for_model,
    display_model_name as display_gemini_model_name,
    display_provider_name as display_gemini_provider_name,
    extract_usage_breakdown as gemini_extract_usage_breakdown,
    price_schedule_for_model as gemini_price_schedule_for_model,
    require_api_key as require_gemini_api_key,
    send_generate_content_request,
    supports_reasoning as gemini_supports_reasoning,
)
from src.providers.anthropic import (
    build_messages_request,
    calculate_cost_breakdown as anthropic_calculate_cost_breakdown,
    default_thinking_budget_for_model as anthropic_default_thinking_budget_for_model,
    display_model_name as display_anthropic_model_name,
    display_provider_name as display_anthropic_provider_name,
    extract_output_text as extract_anthropic_output_text,
    extract_usage_breakdown as anthropic_extract_usage_breakdown,
    price_schedule_for_model as anthropic_price_schedule_for_model,
    require_api_key as require_anthropic_api_key,
    send_messages_request,
    supports_reasoning as anthropic_supports_reasoning,
)
from src.providers.grok import (
    build_chat_completion_request,
    calculate_cost_breakdown as grok_calculate_cost_breakdown,
    display_model_name as display_grok_model_name,
    display_provider_name as display_grok_provider_name,
    extract_output_text as grok_extract_output_text,
    extract_usage_breakdown as grok_extract_usage_breakdown,
    price_schedule_for_model as grok_price_schedule_for_model,
    require_api_key as require_grok_api_key,
    send_chat_completion_request,
)
from src.providers.fireworks import (
    build_chat_completion_request as build_fireworks_chat_completion_request,
    calculate_cost_breakdown as fireworks_calculate_cost_breakdown,
    display_model_name as display_fireworks_model_name,
    display_provider_name as display_fireworks_provider_name,
    extract_output_text as extract_fireworks_output_text,
    extract_usage_breakdown as fireworks_extract_usage_breakdown,
    price_schedule_for_model as fireworks_price_schedule_for_model,
    provider_for_model as fireworks_provider_for_model,
    require_api_key as require_fireworks_api_key,
    resolve_model as resolve_fireworks_model,
    storage_model_name as fireworks_storage_model_name,
    send_chat_completion_request as send_fireworks_chat_completion_request,
)
from src.costs import CostBreakdown, TokenBreakdown, format_cost_line
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


def _format_relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(_repo_root()))
    except ValueError:
        return str(path)


def _format_token_line(
    tokens: TokenBreakdown,
    *,
    max_output_tokens: int | None,
) -> str | None:
    if (
        tokens.input_tokens is None
        and tokens.reasoning_tokens is None
        and tokens.output_tokens is None
    ):
        return None
    input_label = (
        str(tokens.input_tokens)
        if isinstance(tokens.input_tokens, int)
        else "unknown"
    )
    if isinstance(tokens.reasoning_tokens, int):
        reasoning_label = str(tokens.reasoning_tokens)
    elif tokens.reasoning_tokens is None:
        reasoning_label = "0 (disabled)"
    else:
        reasoning_label = "unknown"
    output_label = (
        str(tokens.output_tokens)
        if isinstance(tokens.output_tokens, int)
        else "unknown"
    )
    line = (
        "Actual tokens: "
        f"input={input_label}, thinking={reasoning_label}, output={output_label}"
    )
    if isinstance(tokens.output_tokens, int) and isinstance(max_output_tokens, int):
        if max_output_tokens > 0:
            percent = int(round((tokens.output_tokens / max_output_tokens) * 100))
            line = f"{line} ({percent}% of allowable output)"
    return line


def _print_run_summary(
    *,
    response_payload: dict[str, Any] | None,
    tokens: TokenBreakdown | None,
    cost: CostBreakdown | None,
    max_output_tokens: int | None,
    response_text_path: Path | None,
) -> None:
    if not isinstance(response_payload, dict):
        return
    if response_payload.get("error") is None:
        print("Received complete response with no errors.", flush=True)
    token_line = _format_token_line(tokens, max_output_tokens=max_output_tokens) if tokens else None
    if token_line is not None:
        print(token_line, flush=True)
    if cost is not None:
        print(format_cost_line(cost), flush=True)
    if response_text_path is not None:
        relative_path = _format_relative_path(response_text_path)
        print(f"View problem completion at {relative_path}", flush=True)


def _format_special_setting(name: str, value: float | int | str) -> str:
    if isinstance(value, float) and value.is_integer():
        value_label = str(int(value))
    else:
        value_label = str(value)
    return f"{name}-{value_label}"


def _format_setting_display(
    name: str,
    value: float | int | str,
    *,
    default: float | int | str | None = None,
) -> str:
    if isinstance(value, float) and value.is_integer():
        value_label = str(int(value))
    else:
        value_label = str(value)
    if default is None or value == default:
        return f"'{name}' setting set to {value_label}"
    if isinstance(default, float) and default.is_integer():
        default_label = str(int(default))
    else:
        default_label = str(default)
    return f"'{name}' setting set to {value_label} instead of default {default_label}"


def _gemini_special_settings(
    *,
    explicit: str | None,
    model: str,
    temperature: float | None,
    top_p: float | None,
    top_k: int | None,
) -> tuple[str, str | None]:
    if explicit is not None and str(explicit).strip():
        return normalize_special_settings(explicit), str(explicit)
    settings: list[str] = []
    settings_display: list[str] = []
    if temperature is not None:
        default_temp = gemini_default_temperature_for_model(model)
        if default_temp is None or temperature != default_temp:
            settings.append(_format_special_setting("temperature", temperature))
            settings_display.append(
                _format_setting_display(
                    "temperature",
                    temperature,
                    default=default_temp,
                )
            )
    if top_p is not None:
        settings.append(_format_special_setting("top_p", top_p))
        settings_display.append(_format_setting_display("top_p", top_p))
    if top_k is not None:
        settings.append(_format_special_setting("top_k", top_k))
        settings_display.append(_format_setting_display("top_k", top_k))
    if not settings:
        return "default", None
    return (
        normalize_special_settings(",".join(settings)),
        "; ".join(settings_display),
    )


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
        if debug_sse_path is not None:
            sse_event_path = debug_sse_path
        else:
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
    reasoning_summary = extract_reasoning_summary_from_stream(stream_capture)
    if isinstance(reasoning_summary, str) and reasoning_summary:
        outputs = (
            response_payload.get("output")
            if isinstance(response_payload, dict)
            else None
        )
        if isinstance(outputs, list):
            for item in outputs:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "reasoning":
                    continue
                existing_summary = item.get("summary")
                if existing_summary:
                    break
                item["summary"] = [
                    {"type": "summary_text", "text": reasoning_summary}
                ]
                break
    if stream and isinstance(max_tokens, int):
        print("", flush=True)
    request_completed_at = utc_now_iso()
    output_text = extract_output_text(response_payload)
    if stream and streamed_chunks and not output_text:
        output_text = "".join(streamed_chunks)
    usage_breakdown = (
        openai_extract_usage_breakdown(response_payload)
        if isinstance(response_payload, dict)
        else None
    )
    cost_breakdown = (
        openai_calculate_cost_breakdown(response_payload, model=model)
        if isinstance(response_payload, dict)
        else None
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
    _print_run_summary(
        response_payload=response_payload if isinstance(response_payload, dict) else None,
        tokens=usage_breakdown,
        cost=cost_breakdown,
        max_output_tokens=max_tokens if isinstance(max_tokens, int) else None,
        response_text_path=stored_text.path if stored_text else None,
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


def run_fireworks_puzzle(
    *,
    puzzle_name: str,
    model: str = "deepseek-v3p2",
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    reasoning_effort: str | None = None,
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
    model_id = resolve_fireworks_model(model)
    storage_model = fireworks_storage_model_name(model_id)
    provider = fireworks_provider_for_model(model_id)
    special_settings_label = normalize_special_settings(special_settings)

    if debug_sse and not stream:
        raise ValueError("debug_sse requires stream=True")

    request_payload = build_fireworks_chat_completion_request(
        system_prompt=system_prompt.text,
        user_prompt=puzzle.text,
        model=model_id,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        reasoning_effort=reasoning_effort,
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
            model=storage_model,
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
        f"requesting puzzle={puzzle.name} model={model_id}",
        flush=True,
    )
    max_tokens = request_payload.get("max_tokens")
    if stream and max_tokens is None:
        print("Set max tokens to see streaming info.", flush=True)
    progress_callback = _build_progress_callback(max_tokens, suffix="chars")

    streamed_chunks: list[str] = []

    def _collect_delta(delta: str) -> None:
        streamed_chunks.append(delta)

    sse_event_path = None
    if debug_sse:
        if debug_sse_path is not None:
            sse_event_path = debug_sse_path
        else:
            base_dir = _repo_root() / "tmp"
            timestamp = _format_timestamp(created_at)
            sse_event_path = (
                base_dir / f"fireworks-sse-{storage_model}-{run_id}-{timestamp}.jsonl"
            )
        print(f"DEBUG MODE: skips responses; writing SSE events to {sse_event_path}")

    stream_capture: dict[str, Any] | None = {} if stream else None
    response_payload = send_fireworks_chat_completion_request(
        request_payload,
        api_key=api_key or require_fireworks_api_key(),
        progress_callback=progress_callback if stream else None,
        stream_text_callback=_collect_delta if stream else None,
        sse_event_path=sse_event_path,
        stream_capture=stream_capture,
    )
    if stream and isinstance(max_tokens, int):
        print("", flush=True)
    request_completed_at = utc_now_iso()
    output_text = extract_fireworks_output_text(response_payload)
    if stream and streamed_chunks and not output_text:
        output_text = "".join(streamed_chunks)
    usage_breakdown = (
        fireworks_extract_usage_breakdown(response_payload)
        if isinstance(response_payload, dict)
        else None
    )
    cost_breakdown = (
        fireworks_calculate_cost_breakdown(response_payload, model=model_id)
        if isinstance(response_payload, dict)
        else None
    )
    input_text = format_input_text(system_prompt.text, puzzle.text)
    derived: dict[str, Any] = {
        "timing": {
            "request_started_at": request_started_at,
            "request_completed_at": request_completed_at,
        }
    }
    price_schedule = fireworks_price_schedule_for_model(model_id)
    if price_schedule is not None:
        derived["price_schedule"] = price_schedule
    derived["model_alias"] = display_fireworks_model_name(model_id)
    stored_text = None
    if store is not None:
        stored_text = store.record_response(
            run_id=run_id,
            created_at=created_at,
            provider=provider,
            model=storage_model,
            model_alias=display_fireworks_model_name(storage_model),
            provider_alias=display_fireworks_provider_name(provider),
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

    _print_run_summary(
        response_payload=response_payload if isinstance(response_payload, dict) else None,
        tokens=usage_breakdown,
        cost=cost_breakdown,
        max_output_tokens=max_tokens if isinstance(max_tokens, int) else None,
        response_text_path=stored_text.path if stored_text else None,
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


def run_grok_puzzle(
    *,
    puzzle_name: str,
    model: str = "grok-4-1-fast-reasoning",
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    stream: bool = False,
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
    provider = "grok"
    special_settings_label = normalize_special_settings(special_settings)

    if debug_sse and not stream:
        raise ValueError("debug_sse requires stream=True")

    request_payload = build_chat_completion_request(
        system_prompt=system_prompt.text,
        user_prompt=puzzle.text,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
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
    if not stream:
        print(
            "Streaming turned off for Grok, in order to retain usage stats. "
            "If connections drop, turn on with --streaming true.",
            flush=True,
        )
    max_tokens = request_payload.get("max_tokens")
    if stream and max_tokens is None:
        print("Set max tokens to see streaming info.", flush=True)
    progress_callback = _build_progress_callback(max_tokens, suffix="tokens")

    streamed_chunks: list[str] = []

    def _collect_delta(delta: str) -> None:
        streamed_chunks.append(delta)

    sse_event_path = None
    if debug_sse:
        if debug_sse_path is not None:
            sse_event_path = debug_sse_path
        else:
            base_dir = _repo_root() / "tmp"
            timestamp = _format_timestamp(created_at)
            sse_event_path = (
                base_dir / f"grok-sse-{model}-{run_id}-{timestamp}.jsonl"
            )
        print(f"DEBUG MODE: skips responses; writing SSE events to {sse_event_path}")

    response_payload = send_chat_completion_request(
        request_payload,
        api_key=api_key or require_grok_api_key(),
        progress_callback=progress_callback if stream else None,
        stream_text_callback=_collect_delta if stream else None,
        sse_event_path=sse_event_path,
    )
    if stream and isinstance(max_tokens, int):
        print("", flush=True)
    request_completed_at = utc_now_iso()
    output_text = grok_extract_output_text(response_payload)
    if stream and streamed_chunks and not output_text:
        output_text = "".join(streamed_chunks)
    usage_breakdown = (
        grok_extract_usage_breakdown(response_payload)
        if isinstance(response_payload, dict)
        else None
    )
    cost_breakdown = (
        grok_calculate_cost_breakdown(response_payload, model=model)
        if isinstance(response_payload, dict)
        else None
    )
    input_text = format_input_text(system_prompt.text, puzzle.text)
    derived: dict[str, Any] = {
        "timing": {
            "request_started_at": request_started_at,
            "request_completed_at": request_completed_at,
        }
    }
    price_schedule = grok_price_schedule_for_model(model)
    if price_schedule is not None:
        derived["price_schedule"] = price_schedule
    derived["model_alias"] = display_grok_model_name(model)
    stored_text = None
    if store is not None:
        stored_text = store.record_response(
            run_id=run_id,
            created_at=created_at,
            provider=provider,
            model=model,
            model_alias=display_grok_model_name(model),
            provider_alias=display_grok_provider_name(provider),
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
    _print_run_summary(
        response_payload=response_payload if isinstance(response_payload, dict) else None,
        tokens=usage_breakdown,
        cost=cost_breakdown,
        max_output_tokens=max_tokens if isinstance(max_tokens, int) else None,
        response_text_path=stored_text.path if stored_text else None,
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
    provider = "gemini"
    special_settings_label, special_settings_display = _gemini_special_settings(
        explicit=special_settings,
        model=model,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
    )

    if debug_sse and not stream:
        raise ValueError("debug_sse requires stream=True")

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

    sse_event_path = None
    if debug_sse:
        if debug_sse_path is not None:
            sse_event_path = debug_sse_path
        else:
            base_dir = _repo_root() / "tmp"
            timestamp = _format_timestamp(created_at)
            sse_event_path = (
                base_dir / f"gemini-sse-{model}-{run_id}-{timestamp}.jsonl"
            )
        print(f"DEBUG MODE: skips responses; writing SSE events to {sse_event_path}")

    response = send_generate_content_request(
        request_payload,
        api_key=api_key or require_gemini_api_key(),
        stream=stream,
        stream_text_callback=_collect_delta if stream else None,
        sse_event_path=sse_event_path,
    )
    if stream and isinstance(max_tokens, int):
        print("", flush=True)
    request_completed_at = utc_now_iso()
    output_text = response.output_text
    usage_breakdown = (
        gemini_extract_usage_breakdown(response.payload)
        if isinstance(response.payload, dict)
        else None
    )
    cost_breakdown = (
        gemini_calculate_cost_breakdown(response.payload, model=model)
        if isinstance(response.payload, dict)
        else None
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
    stored_text = None
    if store is not None:
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
            special_settings_display=special_settings_display,
            request_payload=request_payload,
            response_payload=response.payload,
            input_text=input_text,
            output_text=output_text,
            derived=derived,
        )
    _print_run_summary(
        response_payload=response.payload if isinstance(response.payload, dict) else None,
        tokens=usage_breakdown,
        cost=cost_breakdown,
        max_output_tokens=max_tokens if isinstance(max_tokens, int) else None,
        response_text_path=stored_text.path if stored_text else None,
    )
    return RunResult(
        run_id=run_id,
        request_payload=request_payload,
        response_payload=response.payload,
        output_text=output_text,
        request_path=request_path,
        response_text_path=stored_text.path if stored_text else None,
        sse_event_path=sse_event_path,
    )


def run_anthropic_puzzle(
    *,
    puzzle_name: str,
    model: str = "claude-opus-4-5-20251101",
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    thinking: dict[str, Any] | None = None,
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
    provider = "anthropic"
    special_settings_label = normalize_special_settings(special_settings)

    if debug_sse and not stream:
        raise ValueError("debug_sse requires stream=True")

    if thinking is None and anthropic_supports_reasoning(model):
        budget_tokens = anthropic_default_thinking_budget_for_model(model)
        if budget_tokens is not None:
            thinking = {"type": "enabled", "budget_tokens": budget_tokens}

    request_payload = build_messages_request(
        system_prompt=system_prompt.text,
        user_prompt=puzzle.text,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        thinking=thinking,
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
        f"Requesting model {model} for puzzle '{puzzle.name}'",
        flush=True,
    )
    max_tokens = request_payload.get("max_tokens")
    progress_callback = _build_progress_callback(
        max_tokens if isinstance(max_tokens, int) else None,
        suffix="total possible",
    )

    sse_event_path = None
    if debug_sse:
        if debug_sse_path is not None:
            sse_event_path = debug_sse_path
        else:
            base_dir = _repo_root() / "tmp"
            timestamp = _format_timestamp(created_at)
            sse_event_path = (
                base_dir / f"anthropic-sse-{model}-{run_id}-{timestamp}.jsonl"
            )
        print(f"DEBUG MODE: skips responses; writing SSE events to {sse_event_path}")

    response = send_messages_request(
        request_payload,
        api_key=api_key or require_anthropic_api_key(),
        progress_callback=progress_callback if stream else None,
        sse_event_path=sse_event_path,
    )
    if stream and isinstance(max_tokens, int):
        print("", flush=True)
    request_completed_at = utc_now_iso()
    output_text = response.output_text
    if not output_text and isinstance(response.payload, dict):
        output_text = extract_anthropic_output_text(response.payload)
    usage_breakdown = (
        anthropic_extract_usage_breakdown(response.payload)
        if isinstance(response.payload, dict)
        else None
    )
    cost_breakdown = (
        anthropic_calculate_cost_breakdown(response.payload, model=model)
        if isinstance(response.payload, dict)
        else None
    )
    input_text = format_input_text(system_prompt.text, puzzle.text)
    derived: dict[str, Any] = {
        "timing": {
            "request_started_at": request_started_at,
            "request_completed_at": request_completed_at,
        }
    }
    price_schedule = anthropic_price_schedule_for_model(model)
    if price_schedule is not None:
        derived["price_schedule"] = price_schedule
    derived["model_alias"] = display_anthropic_model_name(model)
    stored_text = None
    if store is not None:
        stored_text = store.record_response(
            run_id=run_id,
            created_at=created_at,
            provider=provider,
            model=model,
            model_alias=display_anthropic_model_name(model),
            provider_alias=display_anthropic_provider_name(provider),
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
    _print_run_summary(
        response_payload=response.payload if isinstance(response.payload, dict) else None,
        tokens=usage_breakdown,
        cost=cost_breakdown,
        max_output_tokens=max_tokens if isinstance(max_tokens, int) else None,
        response_text_path=stored_text.path if stored_text else None,
    )
    return RunResult(
        run_id=run_id,
        request_payload=request_payload,
        response_payload=response.payload,
        output_text=output_text,
        request_path=request_path,
        response_text_path=stored_text.path if stored_text else None,
        sse_event_path=sse_event_path,
    )
