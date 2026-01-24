"""xAI Grok Chat Completions adapter."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Callable, Iterator
import urllib.error
import urllib.request

from src.costs import CostBreakdown, TokenBreakdown, compute_cost_breakdown


DEFAULT_BASE_URL = "https://api.x.ai/v1/chat/completions"

MODEL_DEFAULTS: dict[str, dict[str, int | None]] = {
    "grok-4-1-fast-reasoning": {"max_output_tokens": 256000},
    "grok-3": {"max_output_tokens": 16384},
}

SUPPORTED_MODELS: set[str] = set(MODEL_DEFAULTS.keys())

MODEL_ALIASES: dict[str, str] = {
    "grok-4-1-fast-reasoning": "Grok 4.1 Fast Reasoning",
    "grok-3": "Grok 3",
}

PROVIDER_ALIASES: dict[str, str] = {
    "grok": "xAI",
}

REASONING_MODELS: set[str] = {"grok-4-1-fast-reasoning"}

PRICE_SCHEDULES_USD_PER_MILLION: dict[str, dict[str, float | None]] = {
    "grok-4-1-fast-reasoning": {"input": 0.20, "output": 0.50},
    "grok-3": {"input": 3.0, "output": 15.0},
}


@dataclass(frozen=True)
class GrokResponse:
    payload: dict[str, Any]
    output_text: str


def require_api_key(env_var: str = "XAI_API_KEY") -> str:
    api_key = os.getenv(env_var)
    if not api_key:
        raise EnvironmentError(f"Missing {env_var} for xAI API access")
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


def extract_usage_breakdown(payload: dict[str, Any]) -> TokenBreakdown | None:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None
    input_tokens = usage.get("prompt_tokens")
    if not isinstance(input_tokens, int):
        input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("completion_tokens")
    if not isinstance(output_tokens, int):
        output_tokens = usage.get("output_tokens")
    reasoning_tokens = None
    for details in (
        usage.get("completion_tokens_details"),
        usage.get("output_tokens_details"),
    ):
        if isinstance(details, dict):
            candidate = details.get("reasoning_tokens")
            if isinstance(candidate, int):
                reasoning_tokens = candidate
                break
    return TokenBreakdown(
        input_tokens=input_tokens if isinstance(input_tokens, int) else None,
        reasoning_tokens=reasoning_tokens,
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


def build_chat_completion_request(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    stream: bool | None = None,
) -> dict[str, Any]:
    if max_output_tokens is None:
        defaults = MODEL_DEFAULTS.get(model, {})
        max_output_tokens = defaults.get("max_output_tokens")

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if max_output_tokens is not None:
        payload["max_tokens"] = max_output_tokens
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if stream is not None:
        payload["stream"] = stream
    return payload


def _iter_sse_events(response: Any) -> Iterator[dict[str, Any]]:
    data_lines: list[str] = []
    while True:
        line_bytes = response.readline()
        if not line_bytes:
            if data_lines:
                data = "\n".join(data_lines)
                data_lines = []
                if data == "[DONE]":
                    break
                yield _parse_sse_data(data)
            break
        line = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
        if not line:
            if data_lines:
                data = "\n".join(data_lines)
                data_lines = []
                if data == "[DONE]":
                    break
                yield _parse_sse_data(data)
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data_lines.append(line[len("data:"):].lstrip())


def _parse_sse_data(data: str) -> dict[str, Any]:
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse Grok stream event: {data}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Unexpected Grok stream event payload: {parsed}")
    return parsed


def _reconstruct_stream_payload(
    events: list[dict[str, Any]], *, model: str | None
) -> dict[str, Any]:
    response_payload: dict[str, Any] = {}
    chunks: list[str] = []
    finish_reason: str | None = None
    choice_index: int | None = None
    role = "assistant"

    for event in events:
        if "id" in event:
            response_payload["id"] = event.get("id")
        if "created" in event:
            response_payload["created"] = event.get("created")
        if "model" in event:
            response_payload["model"] = event.get("model")
        if "system_fingerprint" in event:
            response_payload["system_fingerprint"] = event.get("system_fingerprint")
        if isinstance(event.get("usage"), dict):
            response_payload["usage"] = event.get("usage")

        choices = event.get("choices")
        if not isinstance(choices, list):
            continue
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            if choice_index is None and isinstance(choice.get("index"), int):
                choice_index = choice.get("index")
            delta = choice.get("delta")
            if isinstance(delta, dict):
                content = delta.get("content")
                if isinstance(content, str):
                    chunks.append(content)
                if isinstance(delta.get("role"), str):
                    role = delta.get("role")
            if choice.get("finish_reason") is not None:
                finish_reason = choice.get("finish_reason")

    payload_model = response_payload.get("model")
    if not isinstance(payload_model, str) and isinstance(model, str):
        response_payload["model"] = model
    response_payload["object"] = "chat.completion"
    response_payload["choices"] = [
        {
            "index": choice_index if isinstance(choice_index, int) else 0,
            "message": {"role": role, "content": "".join(chunks)},
            "finish_reason": finish_reason,
        }
    ]
    return response_payload


def extract_output_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list):
        return ""
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
    return ""


def send_chat_completion_request(
    payload: dict[str, Any],
    *,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = 3600,
    progress_callback: Callable[[int], None] | None = None,
    stream_text_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "llm-philosophy/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            if payload.get("stream") is True:
                events: list[dict[str, Any]] = []
                streamed_chars = 0
                for event in _iter_sse_events(response):
                    events.append(event)
                    choices = event.get("choices")
                    if not isinstance(choices, list):
                        continue
                    for choice in choices:
                        if not isinstance(choice, dict):
                            continue
                        delta = choice.get("delta")
                        if not isinstance(delta, dict):
                            continue
                        text = delta.get("content")
                        if isinstance(text, str):
                            streamed_chars += len(text)
                            if stream_text_callback is not None:
                                stream_text_callback(text)
                            if progress_callback is not None:
                                progress_callback(streamed_chars)
                response_payload = _reconstruct_stream_payload(
                    events,
                    model=payload.get("model") if isinstance(payload.get("model"), str) else None,
                )
                output_text = extract_output_text(response_payload)
                if progress_callback is not None and output_text:
                    progress_callback(len(output_text))
                return response_payload
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Grok API error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Grok API connection error: {exc}") from exc
    payload = json.loads(body)
    return payload


def create_chat_completion(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None,
    temperature: float | None = None,
    top_p: float | None = None,
    stream: bool | None = None,
    api_key: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = 3600,
) -> GrokResponse:
    payload = build_chat_completion_request(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        stream=stream,
    )
    response_payload = send_chat_completion_request(
        payload,
        api_key=api_key or require_api_key(),
        base_url=base_url,
        timeout_s=timeout_s,
    )
    return GrokResponse(
        payload=response_payload,
        output_text=extract_output_text(response_payload),
    )
