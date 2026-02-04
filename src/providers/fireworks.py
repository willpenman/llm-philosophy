"""Fireworks Chat Completions API adapter with reasoning support."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Callable

from fireworks import Fireworks

from src.costs import CostBreakdown, TokenBreakdown, compute_cost_breakdown


CANONICAL_MODELS: dict[str, str] = {
    "deepseek-v3p2": "accounts/fireworks/models/deepseek-v3p2",
    "deepseek-v3-0324": "accounts/fireworks/models/deepseek-v3-0324",
    "qwen3-vl-235b-thinking": "accounts/fireworks/models/qwen3-vl-235b-a22b-thinking",
    "qwen2p5-vl-32b": "accounts/fireworks/models/qwen2p5-vl-32b-instruct",
    "kimi-k2p5": "accounts/fireworks/models/kimi-k2p5",
    "kimi-k2-instruct-0905": "accounts/fireworks/models/kimi-k2-instruct-0905",
    "llama-v3p3-70b-instruct": "accounts/fireworks/models/llama-v3p3-70b-instruct",
}

REVERSE_CANONICAL_MODELS: dict[str, str] = {
    canonical: alias for alias, canonical in CANONICAL_MODELS.items()
}

MODEL_DEFAULTS: dict[str, dict[str, int | None]] = {
    "accounts/fireworks/models/deepseek-v3p2": {"max_output_tokens": 64000},
    "accounts/fireworks/models/deepseek-v3-0324": {"max_output_tokens": 30000},
    "accounts/fireworks/models/qwen3-vl-235b-a22b-thinking": {"max_output_tokens": 38912},
    "accounts/fireworks/models/qwen2p5-vl-32b-instruct": {"max_output_tokens": 128000},
    "accounts/fireworks/models/kimi-k2p5": {"max_output_tokens": 250000},
    "accounts/fireworks/models/kimi-k2-instruct-0905": {"max_output_tokens": 250000},
    "accounts/fireworks/models/llama-v3p3-70b-instruct": {"max_output_tokens": 8192},
}

SUPPORTED_MODELS: set[str] = set(MODEL_DEFAULTS.keys()) | set(CANONICAL_MODELS.keys())

REASONING_MODELS: set[str] = {
    "accounts/fireworks/models/deepseek-v3p2",
    "deepseek-v3p2",
    "accounts/fireworks/models/qwen3-vl-235b-a22b-thinking",
    "qwen3-vl-235b-thinking",
    "accounts/fireworks/models/kimi-k2p5",
    "kimi-k2p5",
    "accounts/fireworks/models/kimi-k2-instruct-0905",
    "kimi-k2-instruct-0905",
}

PRICE_SCHEDULES_USD_PER_MILLION: dict[str, dict[str, float | None]] = {
    "accounts/fireworks/models/deepseek-v3p2": {
        "input": 0.56,
        "input_cached": 0.28,
        "output": 1.68,
    },
    "accounts/fireworks/models/deepseek-v3-0324": {
        "input": 0.90,
        "input_cached": 0.45,
        "output": 0.90,
    },
    "accounts/fireworks/models/qwen3-vl-235b-a22b-thinking": {
        "input": 0.22,
        "input_cached": None,
        "output": 0.88,
    },
    "accounts/fireworks/models/qwen2p5-vl-32b-instruct": {
        "input": 0.90,
        "input_cached": 0.45,
        "output": 0.90,
    },
    "accounts/fireworks/models/kimi-k2p5": {
        "input": 0.60,
        "input_cached": 0.10,
        "output": 3.00,
    },
    "accounts/fireworks/models/kimi-k2-instruct-0905": {
        "input": 0.60,
        "input_cached": 0.30,
        "output": 2.50,
    },
    "accounts/fireworks/models/llama-v3p3-70b-instruct": {
        "input": 0.90,
        "input_cached": 0.45,
        "output": 0.90,
    },
}

MODEL_ALIASES: dict[str, str] = {
    "accounts/fireworks/models/deepseek-v3p2": "DeepSeek V3.2",
    "deepseek-v3p2": "DeepSeek V3.2",
    "accounts/fireworks/models/deepseek-v3-0324": "DeepSeek V3 Update 1",
    "deepseek-v3-0324": "DeepSeek V3 Update 1",
    "accounts/fireworks/models/qwen3-vl-235b-a22b-thinking": "Qwen3-VL 235B Thinking",
    "qwen3-vl-235b-thinking": "Qwen3-VL 235B Thinking",
    "accounts/fireworks/models/qwen2p5-vl-32b-instruct": "Qwen2.5-VL 32B",
    "qwen2p5-vl-32b": "Qwen2.5-VL 32B",
    "accounts/fireworks/models/kimi-k2p5": "Kimi K2.5",
    "kimi-k2p5": "Kimi K2.5",
    "accounts/fireworks/models/kimi-k2-instruct-0905": "Kimi K2",
    "kimi-k2-instruct-0905": "Kimi K2",
    "accounts/fireworks/models/llama-v3p3-70b-instruct": "Llama 3.3 70B",
    "llama-v3p3-70b-instruct": "Llama 3.3 70B",
}

MODEL_PROVIDERS: dict[str, str] = {
    "accounts/fireworks/models/deepseek-v3p2": "deepseek",
    "accounts/fireworks/models/deepseek-v3-0324": "deepseek",
    "accounts/fireworks/models/qwen3-vl-235b-a22b-thinking": "qwen",
    "accounts/fireworks/models/qwen2p5-vl-32b-instruct": "qwen",
    "accounts/fireworks/models/kimi-k2p5": "kimi",
    "accounts/fireworks/models/kimi-k2-instruct-0905": "kimi",
    "accounts/fireworks/models/llama-v3p3-70b-instruct": "meta",
}

PROVIDER_ALIASES: dict[str, str] = {
    "deepseek": "DeepSeek AI (via Fireworks)",
    "qwen": "Qwen (via Fireworks)",
    "kimi": "Moonshot AI (via Fireworks)",
    "meta": "Meta (via Fireworks)",
    "fireworks": "Fireworks",
}


@dataclass(frozen=True)
class FireworksResponse:
    payload: dict[str, Any]
    output_text: str
    reasoning_content: str | None


def require_api_key(env_var: str = "FIREWORKS_API_KEY") -> str:
    api_key = os.getenv(env_var)
    if not api_key:
        raise EnvironmentError(f"Missing {env_var} for Fireworks API access")
    return api_key


def provider_for_model(model: str) -> str:
    model_id = CANONICAL_MODELS.get(model, model)
    return MODEL_PROVIDERS.get(model_id, "fireworks")


def resolve_model(model: str) -> str:
    return CANONICAL_MODELS.get(model, model)


def storage_model_name(model: str) -> str:
    if model in CANONICAL_MODELS:
        return model
    return REVERSE_CANONICAL_MODELS.get(model, model)


def price_schedule_for_model(model: str) -> dict[str, Any] | None:
    schedule = PRICE_SCHEDULES_USD_PER_MILLION.get(resolve_model(model))
    if schedule is None:
        return None
    return {
        "currency": "usd",
        "unit": "per_million_tokens",
        "input": schedule["input"],
        "input_cached": schedule.get("input_cached"),
        "output": schedule["output"],
    }


def display_model_name(model: str) -> str:
    return MODEL_ALIASES.get(model, model)


def display_provider_name(provider: str) -> str:
    return PROVIDER_ALIASES.get(provider, provider)


def supports_reasoning(model: str) -> bool:
    return model in REASONING_MODELS or resolve_model(model) in REASONING_MODELS


def supports_model(model: str) -> bool:
    return model in SUPPORTED_MODELS


def default_reasoning_effort_for_model(model: str) -> str | None:
    """Return default reasoning_effort for reasoning models.

    For DeepSeek V3.2: any value other than 'none' enables reasoning output.
    Other reasoning models may support 'low', 'medium', 'high'.
    """
    model_id = resolve_model(model)
    if model_id in REASONING_MODELS or model in REASONING_MODELS:
        return "high"
    return None


def build_chat_completion_request(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    reasoning_effort: str | None = None,
    stream: bool | None = None,
) -> dict[str, Any]:
    model_id = resolve_model(model)
    if max_output_tokens is None:
        defaults = MODEL_DEFAULTS.get(model_id, {})
        max_output_tokens = defaults.get("max_output_tokens")

    # Default to enabling reasoning for reasoning models
    if reasoning_effort is None:
        reasoning_effort = default_reasoning_effort_for_model(model_id)

    payload: dict[str, Any] = {
        "model": model_id,
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
    if reasoning_effort is not None:
        payload["reasoning_effort"] = reasoning_effort
    if stream is not None:
        payload["stream"] = stream
    return payload


def _model_dump(value: Any) -> dict[str, Any]:
    """Convert SDK response objects to dictionaries."""
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
    raise TypeError(f"Unsupported Fireworks payload type: {type(value)!r}")


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
    # Check for reasoning tokens in various places Fireworks might put them
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
    schedule = price_schedule_for_model(resolve_model(model))
    if schedule is None:
        return None
    tokens = extract_usage_breakdown(payload)
    if tokens is None:
        return None
    # Reasoning tokens are included in output for cost purposes
    return compute_cost_breakdown(tokens, schedule, output_includes_reasoning=True)


def extract_output_text(payload: dict[str, Any]) -> str:
    """Extract the main output text from a chat completion response."""
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


def extract_reasoning_content(payload: dict[str, Any]) -> str | None:
    """Extract reasoning content from a chat completion response."""
    choices = payload.get("choices")
    if not isinstance(choices, list):
        return None
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            continue
        reasoning = message.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning:
            return reasoning
    return None


def _reconstruct_stream_payload(
    events: list[dict[str, Any]],
    *,
    content_chunks: list[str],
    reasoning_chunks: list[str],
    model: str | None,
) -> dict[str, Any]:
    """Reconstruct a complete response payload from stream events."""
    response_payload: dict[str, Any] = {}
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
            if isinstance(delta, dict) and isinstance(delta.get("role"), str):
                role = delta.get("role")
            if choice.get("finish_reason") is not None:
                finish_reason = choice.get("finish_reason")

    payload_model = response_payload.get("model")
    if not isinstance(payload_model, str) and isinstance(model, str):
        response_payload["model"] = model
    response_payload["object"] = "chat.completion"

    message: dict[str, Any] = {"role": role, "content": "".join(content_chunks)}
    if reasoning_chunks:
        message["reasoning_content"] = "".join(reasoning_chunks)

    response_payload["choices"] = [
        {
            "index": choice_index if isinstance(choice_index, int) else 0,
            "message": message,
            "finish_reason": finish_reason,
        }
    ]
    return response_payload


def send_chat_completion_request(
    payload: dict[str, Any],
    *,
    api_key: str,
    timeout_s: float = 600,
    progress_callback: Callable[[int], None] | None = None,
    stream_text_callback: Callable[[str], None] | None = None,
    stream_reasoning_callback: Callable[[str], None] | None = None,
    sse_event_path: Path | None = None,
    stream_capture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a chat completion request using the Fireworks SDK."""
    try:
        client = Fireworks(api_key=api_key)

        if payload.get("stream") is True:
            events: list[dict[str, Any]] = []
            content_chunks: list[str] = []
            reasoning_chunks: list[str] = []
            streamed_chars = 0

            sse_handle = None
            if sse_event_path is not None:
                sse_event_path.parent.mkdir(parents=True, exist_ok=True)
                sse_handle = sse_event_path.open("a", encoding="utf-8")

            try:
                stream = client.chat.completions.create(**payload, timeout=timeout_s)
                for chunk in stream:
                    event_payload = _model_dump(chunk)
                    events.append(event_payload)

                    if sse_handle is not None:
                        sse_handle.write(json.dumps(event_payload, ensure_ascii=True))
                        sse_handle.write("\n")

                    choices = event_payload.get("choices")
                    if not isinstance(choices, list):
                        continue

                    for choice in choices:
                        if not isinstance(choice, dict):
                            continue
                        delta = choice.get("delta")
                        if not isinstance(delta, dict):
                            continue

                        # Handle reasoning content
                        reasoning = delta.get("reasoning_content")
                        if isinstance(reasoning, str) and reasoning:
                            reasoning_chunks.append(reasoning)
                            if stream_reasoning_callback is not None:
                                stream_reasoning_callback(reasoning)

                        # Handle regular content
                        content = delta.get("content")
                        if isinstance(content, str) and content:
                            content_chunks.append(content)
                            streamed_chars += len(content)
                            if stream_text_callback is not None:
                                stream_text_callback(content)
                            if progress_callback is not None:
                                progress_callback(streamed_chars)

            finally:
                if sse_handle is not None:
                    sse_handle.close()

            # Store reasoning in stream_capture for runner to extract
            if stream_capture is not None:
                stream_capture["reasoning_chunks"] = reasoning_chunks
                stream_capture["content_chunks"] = content_chunks

            response_payload = _reconstruct_stream_payload(
                events,
                content_chunks=content_chunks,
                reasoning_chunks=reasoning_chunks,
                model=payload.get("model") if isinstance(payload.get("model"), str) else None,
            )
            return response_payload

        # Non-streaming request
        response = client.chat.completions.create(**payload, timeout=timeout_s)
        return _model_dump(response)

    except Exception as exc:
        # Wrap SDK errors consistently
        raise RuntimeError(f"Fireworks API error: {exc}") from exc


def create_chat_completion(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    reasoning_effort: str | None = None,
    stream: bool | None = None,
    sse_event_path: Path | None = None,
    api_key: str | None = None,
    timeout_s: float = 600,
) -> FireworksResponse:
    payload = build_chat_completion_request(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        reasoning_effort=reasoning_effort,
        stream=stream,
    )
    response_payload = send_chat_completion_request(
        payload,
        api_key=api_key or require_api_key(),
        timeout_s=timeout_s,
        sse_event_path=sse_event_path,
    )
    return FireworksResponse(
        payload=response_payload,
        output_text=extract_output_text(response_payload),
        reasoning_content=extract_reasoning_content(response_payload),
    )
