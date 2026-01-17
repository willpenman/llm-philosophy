"""Anthropic Messages API adapter."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Callable, Iterator
import urllib.error
import urllib.request

from src.costs import CostBreakdown, TokenBreakdown, compute_cost_breakdown


DEFAULT_BASE_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_VERSION = "2023-06-01"

MODEL_DEFAULTS: dict[str, dict[str, int | None]] = {
    "claude-opus-4-5-20251101": {"max_output_tokens": 64000, "thinking_budget_tokens": 20000},
}

SUPPORTED_MODELS: set[str] = set(MODEL_DEFAULTS.keys())

MODEL_ALIASES: dict[str, str] = {
    "claude-opus-4-5-20251101": "Opus 4.5",
}

PROVIDER_ALIASES: dict[str, str] = {
    "anthropic": "Anthropic",
}

REASONING_MODELS: set[str] = {"claude-opus-4-5-20251101"}

PRICE_SCHEDULES_USD_PER_MILLION: dict[str, dict[str, float | None]] = {
    "claude-opus-4-5-20251101": {"input": 5.0, "output": 25.0},
}


@dataclass(frozen=True)
class AnthropicResponse:
    payload: dict[str, Any]
    output_text: str


def require_api_key(env_var: str = "ANTHROPIC_API_KEY") -> str:
    api_key = os.getenv(env_var)
    if not api_key:
        raise EnvironmentError(f"Missing {env_var} for Anthropic API access")
    return api_key


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


def default_thinking_budget_for_model(model: str) -> int | None:
    defaults = MODEL_DEFAULTS.get(model, {})
    return defaults.get("thinking_budget_tokens")


def extract_usage_breakdown(payload: dict[str, Any]) -> TokenBreakdown | None:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None
    input_tokens = usage.get("input_tokens")
    cache_creation_tokens = usage.get("cache_creation_input_tokens")
    cache_read_tokens = usage.get("cache_read_input_tokens")
    output_tokens = usage.get("output_tokens")
    input_total = None
    if isinstance(input_tokens, int):
        input_total = input_tokens
        if isinstance(cache_creation_tokens, int):
            input_total += cache_creation_tokens
        if isinstance(cache_read_tokens, int):
            input_total += cache_read_tokens
    return TokenBreakdown(
        input_tokens=input_total,
        reasoning_tokens=None,
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


def _system_blocks(system_prompt: str) -> list[dict[str, str]]:
    return [{"type": "text", "text": system_prompt}]


def build_messages_request(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    thinking: dict[str, Any] | None = None,
    stream: bool | None = None,
) -> dict[str, Any]:
    if max_output_tokens is None:
        defaults = MODEL_DEFAULTS.get(model, {})
        max_output_tokens = defaults.get("max_output_tokens")
    if max_output_tokens is None:
        raise ValueError("max_output_tokens must be set for Anthropic requests")
    if thinking is not None and (temperature is not None or top_k is not None):
        raise ValueError("Anthropic thinking is incompatible with temperature or top_k")
    if thinking is not None:
        thinking_type = thinking.get("type")
        if thinking_type != "enabled":
            raise ValueError("Anthropic thinking.type must be 'enabled' when provided")
        budget_tokens = thinking.get("budget_tokens")
        if not isinstance(budget_tokens, int):
            raise ValueError("Anthropic thinking.budget_tokens must be an integer")
        if budget_tokens <= 0:
            raise ValueError("Anthropic thinking.budget_tokens must be positive")
        if budget_tokens >= max_output_tokens:
            raise ValueError(
                "Anthropic thinking.budget_tokens must be less than max_tokens"
            )

    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": max_output_tokens,
        "system": _system_blocks(system_prompt),
        "messages": [{"role": "user", "content": user_prompt}],
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if top_k is not None:
        payload["top_k"] = top_k
    if thinking is not None:
        payload["thinking"] = thinking
    if stream is not None:
        payload["stream"] = stream
    return payload


def _iter_sse_events(response: Any) -> Iterator[dict[str, Any]]:
    event_type: str | None = None
    data_lines: list[str] = []
    while True:
        line_bytes = response.readline()
        if not line_bytes:
            if data_lines:
                yield _parse_sse_event(event_type, data_lines)
            break
        line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
        if not line:
            if data_lines:
                yield _parse_sse_event(event_type, data_lines)
            event_type = None
            data_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_type = line[len("event:"):].strip() or None
            continue
        if line.startswith("data:"):
            data_lines.append(line[len("data:"):].lstrip())
    return


def _parse_sse_event(event_type: str | None, data_lines: list[str]) -> dict[str, Any]:
    data = "\n".join(data_lines)
    if data == "[DONE]":
        return {"event": event_type, "data": {"type": "done"}}
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse Anthropic stream event: {data}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Unexpected Anthropic stream event payload: {parsed}")
    return {"event": event_type, "data": parsed}


def _extract_text_blocks(payload: dict[str, Any]) -> list[str]:
    content = payload.get("content")
    if not isinstance(content, list):
        return []
    chunks: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "text":
            continue
        text = block.get("text")
        if isinstance(text, str):
            chunks.append(text)
    return chunks


def _extract_thinking_blocks(payload: dict[str, Any]) -> list[str]:
    content = payload.get("content")
    if not isinstance(content, list):
        return []
    chunks: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "thinking":
            continue
        thinking = block.get("thinking")
        if isinstance(thinking, str):
            chunks.append(thinking)
    return chunks


def extract_output_text(payload: dict[str, Any]) -> str:
    chunks = _extract_text_blocks(payload)
    return "".join(chunks)


def extract_thinking_text(payload: dict[str, Any]) -> str:
    chunks = _extract_thinking_blocks(payload)
    return "\n\n\n".join(chunks)


def _update_content_block(block: dict[str, Any], delta: dict[str, Any]) -> None:
    delta_type = delta.get("type")
    if delta_type == "text_delta":
        text = delta.get("text")
        if isinstance(text, str):
            existing = block.get("text")
            block["text"] = f"{existing}{text}" if isinstance(existing, str) else text
    elif delta_type == "thinking_delta":
        thinking = delta.get("thinking")
        if isinstance(thinking, str):
            existing = block.get("thinking")
            block["thinking"] = (
                f"{existing}{thinking}" if isinstance(existing, str) else thinking
            )
    elif delta_type == "signature_delta":
        signature = delta.get("signature")
        if isinstance(signature, str):
            block["signature"] = signature
    elif delta_type == "input_json_delta":
        partial = delta.get("partial_json")
        if isinstance(partial, str):
            existing = block.get("partial_json")
            block["partial_json"] = (
                f"{existing}{partial}" if isinstance(existing, str) else partial
            )


def _reconstruct_stream_payload(events: list[dict[str, Any]]) -> dict[str, Any]:
    response_payload: dict[str, Any] = {}
    content_blocks: dict[int, dict[str, Any]] = {}

    for event in events:
        data_payload = event.get("data")
        if not isinstance(data_payload, dict):
            continue
        event_type = event.get("event") or data_payload.get("type")
        if event_type == "message_start":
            message = data_payload.get("message")
            if isinstance(message, dict):
                response_payload = dict(message)
        elif event_type == "content_block_start":
            index = data_payload.get("index")
            block = data_payload.get("content_block")
            if isinstance(index, int) and isinstance(block, dict):
                content_blocks[index] = dict(block)
        elif event_type == "content_block_delta":
            index = data_payload.get("index")
            delta = data_payload.get("delta")
            if not isinstance(index, int) or not isinstance(delta, dict):
                continue
            block = content_blocks.setdefault(index, {"type": delta.get("type")})
            _update_content_block(block, delta)
        elif event_type == "message_delta":
            delta = data_payload.get("delta")
            if isinstance(delta, dict):
                if "stop_reason" in delta:
                    response_payload["stop_reason"] = delta.get("stop_reason")
                if "stop_sequence" in delta:
                    response_payload["stop_sequence"] = delta.get("stop_sequence")
            usage = data_payload.get("usage")
            if isinstance(usage, dict):
                response_payload["usage"] = usage

    if content_blocks:
        response_payload["content"] = [
            content_blocks[index] for index in sorted(content_blocks.keys())
        ]
    return response_payload


def send_messages_request(
    payload: dict[str, Any],
    *,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    api_version: str = DEFAULT_VERSION,
    timeout_s: float = 60,
    progress_callback: Callable[[int], None] | None = None,
) -> AnthropicResponse:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url,
        data=data,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": api_version,
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            if payload.get("stream") is True:
                events: list[dict[str, Any]] = []
                streamed_chars = 0
                for event in _iter_sse_events(response):
                    events.append(event)
                    if progress_callback is None:
                        continue
                    data_payload = event.get("data")
                    if not isinstance(data_payload, dict):
                        continue
                    event_type = event.get("event") or data_payload.get("type")
                    if event_type != "content_block_delta":
                        continue
                    delta = data_payload.get("delta")
                    if not isinstance(delta, dict):
                        continue
                    if delta.get("type") != "text_delta":
                        continue
                    text = delta.get("text")
                    if isinstance(text, str):
                        streamed_chars += len(text)
                        progress_callback(streamed_chars)
                response_payload = _reconstruct_stream_payload(events)
                output_text = extract_output_text(response_payload)
                if progress_callback is not None and output_text:
                    progress_callback(len(output_text))
                return AnthropicResponse(payload=response_payload, output_text=output_text)
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic API error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Anthropic API connection error: {exc}") from exc
    payload = json.loads(body)
    output_text = extract_output_text(payload) if isinstance(payload, dict) else ""
    return AnthropicResponse(payload=payload, output_text=output_text)
