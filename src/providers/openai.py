"""OpenAI Responses API adapter."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Callable

from openai import APIConnectionError, APIStatusError, OpenAI, OpenAIError

from src.costs import CostBreakdown, TokenBreakdown, compute_cost_breakdown


DEFAULT_BASE_URL = "https://api.openai.com/v1"

MODEL_DEFAULTS: dict[str, dict[str, int | None]] = {
    "o3-2025-04-16": {"max_output_tokens": 100000},
    "gpt-4o-2024-05-13": {"max_output_tokens": 64000},
    "gpt-5.2-2025-12-11": {"max_output_tokens": 128000},
}

SUPPORTED_MODELS: set[str] = set(MODEL_DEFAULTS.keys())

PRICE_SCHEDULES_USD_PER_MILLION: dict[str, dict[str, float | None]] = {
    "o3-2025-04-16": {"input": 2.0, "output": 8.0},
    "gpt-4o-2024-05-13": {"input": 2.5, "output": 10.0},
    "gpt-5.2-2025-12-11": {"input": 1.75, "output": 14.0},
}

MODEL_ALIASES: dict[str, str] = {
    "o3-2025-04-16": "o3",
    "gpt-4o-2024-05-13": "4o",
    "gpt-5.2-2025-12-11": "GPT 5.2",
}

PROVIDER_ALIASES: dict[str, str] = {
    "openai": "OpenAI",
}

REASONING_MODELS: set[str] = {"o3-2025-04-16", "gpt-5.2-2025-12-11"}

@dataclass(frozen=True)
class OpenAIResponse:
    payload: dict[str, Any]
    output_text: str


def require_api_key(env_var: str = "OPENAI_API_KEY") -> str:
    api_key = os.getenv(env_var)
    if not api_key:
        raise EnvironmentError(f"Missing {env_var} for OpenAI API access")
    return api_key


def _normalize_base_url(base_url: str) -> str:
    if base_url.endswith("/responses"):
        return base_url[: -len("/responses")]
    return base_url


def price_schedule_for_model(model: str) -> dict[str, Any] | None:
    schedule = PRICE_SCHEDULES_USD_PER_MILLION.get(model)
    if schedule is None:
        return None
    return {
        "currency": "usd",
        "unit": "per_million_tokens",
        "input": schedule["input"],
        "output": schedule["output"],
    }


def display_model_name(model: str) -> str:
    return MODEL_ALIASES.get(model, model)


def display_provider_name(provider: str) -> str:
    return PROVIDER_ALIASES.get(provider, provider)


def supports_reasoning(model: str) -> bool:
    return model in REASONING_MODELS


def supports_model(model: str) -> bool:
    return model in SUPPORTED_MODELS


def extract_usage_breakdown(payload: dict[str, Any]) -> TokenBreakdown | None:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    reasoning_tokens = None
    details = usage.get("output_tokens_details")
    if isinstance(details, dict):
        reasoning_tokens = details.get("reasoning_tokens")
    return TokenBreakdown(
        input_tokens=input_tokens if isinstance(input_tokens, int) else None,
        reasoning_tokens=reasoning_tokens if isinstance(reasoning_tokens, int) else None,
        output_tokens=output_tokens if isinstance(output_tokens, int) else None,
    )


def calculate_cost_breakdown(payload: dict[str, Any], *, model: str) -> CostBreakdown | None:
    schedule = price_schedule_for_model(model)
    if schedule is None:
        return None
    tokens = extract_usage_breakdown(payload)
    if tokens is None:
        return None
    return compute_cost_breakdown(tokens, schedule, output_includes_reasoning=True)


def _content_item(text: str) -> dict[str, str]:
    return {"type": "input_text", "text": text}


def build_response_request(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None,
    temperature: float | None = None,
    top_p: float | None = None,
    reasoning: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: dict[str, Any] | str | None = None,
    seed: int | None = None,
    metadata: dict[str, Any] | None = None,
    stream: bool | None = None,
    stream_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if max_output_tokens is None:
        defaults = MODEL_DEFAULTS.get(model, {})
        max_output_tokens = defaults.get("max_output_tokens")
    if max_output_tokens is None:
        raise ValueError(
            "max_output_tokens must be set (model defaults are not yet configured)"
        )

    payload: dict[str, Any] = {
        "model": model,
        "input": [
            {"role": "system", "content": [_content_item(system_prompt)]},
            {"role": "user", "content": [_content_item(user_prompt)]},
        ],
        "max_output_tokens": max_output_tokens,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if reasoning is not None:
        payload["reasoning"] = reasoning
    if tools:
        payload["tools"] = tools
    if tool_choice is not None:
        payload["tool_choice"] = tool_choice
    if seed is not None:
        payload["seed"] = seed
    if metadata:
        payload["metadata"] = metadata
    if stream is not None:
        payload["stream"] = stream
    if stream_options is not None:
        payload["stream_options"] = stream_options
    return payload


def _model_dump(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        try:
            return dump(mode="json", exclude_none=True, warnings="none")
        except TypeError:
            return dump()
    legacy_dump = getattr(value, "dict", None)
    if callable(legacy_dump):
        return legacy_dump()
    raise TypeError(f"Unsupported OpenAI payload type: {type(value)!r}")


def _extract_output_text_from_stream(events: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    response_payload: dict[str, Any] | None = None
    for event in events:
        event_type = event.get("type")
        if event_type == "response.output_text.delta":
            delta = event.get("delta")
            if isinstance(delta, str):
                chunks.append(delta)
        elif event_type in {"response.output_text.done", "response.text.done"}:
            if not chunks:
                text = event.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        elif event_type == "response.completed":
            response = event.get("response")
            if isinstance(response, dict):
                response_payload = response
    if chunks:
        return "".join(chunks)
    if response_payload:
        return extract_output_text(response_payload)
    return ""


def _coalesce_reasoning_summary_parts(
    *,
    done_order: list[tuple[int | None, str]],
    delta_chunks: dict[int, list[str]],
) -> list[str]:
    parts: list[str] = []
    used_indices: set[int] = set()
    for index, text in done_order:
        if isinstance(text, str) and text:
            parts.append(text)
            if isinstance(index, int):
                used_indices.add(index)
            continue
        if isinstance(index, int):
            deltas = delta_chunks.get(index)
            if isinstance(deltas, list) and deltas:
                parts.append("".join(deltas))
                used_indices.add(index)
    for index in sorted(delta_chunks):
        if index in used_indices:
            continue
        deltas = delta_chunks.get(index)
        if isinstance(deltas, list) and deltas:
            parts.append("".join(deltas))
    return parts


def extract_reasoning_summary_from_stream(
    stream_capture: dict[str, Any] | None,
) -> str | None:
    if not isinstance(stream_capture, dict):
        return None
    done_order = stream_capture.get("reasoning_summary_done_order")
    delta_chunks = stream_capture.get("reasoning_summary_deltas")
    if not isinstance(done_order, list) or not isinstance(delta_chunks, dict):
        return None
    summary_parts = _coalesce_reasoning_summary_parts(
        done_order=done_order,
        delta_chunks=delta_chunks,
    )
    if not summary_parts:
        return None
    return "\n\n\n".join(summary_parts)


def send_response_request(
    payload: dict[str, Any],
    *,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = 60,
    progress_callback: Callable[[int], None] | None = None,
    stream_text_callback: Callable[[str], None] | None = None,
    sse_event_path: Path | None = None,
    stream_capture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        client = OpenAI(api_key=api_key, base_url=_normalize_base_url(base_url))
        if payload.get("stream") is True:
            streamed_chars = 0
            response_payload: dict[str, Any] | None = None
            summary_chunks: dict[int, list[str]] = {}
            summary_done_order: list[tuple[int | None, str]] = []
            sse_handle = None
            if sse_event_path is not None:
                sse_event_path.parent.mkdir(parents=True, exist_ok=True)
                sse_handle = sse_event_path.open("a", encoding="utf-8")
            try:
                stream = client.responses.create(**payload, timeout=timeout_s)
                for event in stream:
                    event_payload = _model_dump(event)
                    if sse_handle is not None:
                        sse_handle.write(json.dumps(event_payload, ensure_ascii=True))
                        sse_handle.write("\n")
                    event_type = event_payload.get("type")
                    if event_type == "response.output_text.delta":
                        delta = event_payload.get("delta")
                        if isinstance(delta, str):
                            streamed_chars += len(delta)
                            if stream_text_callback is not None:
                                stream_text_callback(delta)
                            if progress_callback is not None:
                                progress_callback(streamed_chars)
                    elif event_type == "response.reasoning_summary_text.delta":
                        delta = event_payload.get("delta")
                        index = event_payload.get("summary_index")
                        if isinstance(delta, str) and isinstance(index, int):
                            summary_chunks.setdefault(index, []).append(delta)
                    elif event_type == "response.reasoning_summary_part.done":
                        index = event_payload.get("summary_index")
                        part = event_payload.get("part")
                        if isinstance(index, int) and isinstance(part, dict):
                            text = part.get("text")
                            if isinstance(text, str):
                                summary_done_order.append((index, text))
                        elif isinstance(part, dict):
                            text = part.get("text")
                            if isinstance(text, str):
                                summary_done_order.append((None, text))
                    elif event_type in {"response.completed", "response.failed"}:
                        response = event_payload.get("response")
                        if isinstance(response, dict):
                            response_payload = response
            finally:
                if sse_handle is not None:
                    sse_handle.close()
            if stream_capture is not None:
                stream_capture["reasoning_summary_done_order"] = summary_done_order
                stream_capture["reasoning_summary_deltas"] = summary_chunks
            return response_payload or {}
        response = client.responses.create(**payload, timeout=timeout_s)
        return _model_dump(response)
    except APIStatusError as exc:
        body = exc.body
        detail = str(exc)
        if body is not None:
            detail = f"{detail} | body={json.dumps(body, ensure_ascii=True)}"
        raise RuntimeError(f"OpenAI API error {exc.status_code}: {detail}") from exc
    except APIConnectionError as exc:
        raise RuntimeError(f"OpenAI API connection error: {exc}") from exc
    except OpenAIError as exc:
        raise RuntimeError(f"OpenAI API error: {exc}") from exc


def extract_output_text(payload: dict[str, Any]) -> str:
    if payload.get("stream") is True:
        events = payload.get("events", [])
        if isinstance(events, list):
            events_list = [event for event in events if isinstance(event, dict)]
            return _extract_output_text_from_stream(events_list)

    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return output_text

    outputs = payload.get("output", [])
    if isinstance(outputs, list):
        chunks: list[str] = []
        for item in outputs:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") != "output_text":
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        if chunks:
            return "\n".join(chunks)
    return ""


def create_response(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None,
    temperature: float | None = None,
    top_p: float | None = None,
    reasoning: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: dict[str, Any] | str | None = None,
    seed: int | None = None,
    metadata: dict[str, Any] | None = None,
    stream: bool | None = None,
    stream_options: dict[str, Any] | None = None,
    sse_event_path: Path | None = None,
    api_key: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = 60,
) -> OpenAIResponse:
    payload = build_response_request(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        reasoning=reasoning,
        tools=tools,
        tool_choice=tool_choice,
        seed=seed,
        metadata=metadata,
        stream=stream,
        stream_options=stream_options,
    )
    response_payload = send_response_request(
        payload,
        api_key=api_key or require_api_key(),
        base_url=base_url,
        timeout_s=timeout_s,
        sse_event_path=sse_event_path,
    )
    return OpenAIResponse(
        payload=response_payload,
        output_text=extract_output_text(response_payload),
    )
