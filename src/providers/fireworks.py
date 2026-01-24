"""Fireworks Responses API adapter (OpenAI-compatible)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Callable

from src.costs import CostBreakdown, TokenBreakdown, compute_cost_breakdown
from src.providers.openai import (
    build_response_request as build_openai_response_request,
    extract_output_text,
    send_response_request as send_openai_response_request,
)


DEFAULT_BASE_URL = "https://api.fireworks.ai/inference/v1"

CANONICAL_MODELS: dict[str, str] = {
    "deepseek-v3p2": "accounts/fireworks/models/deepseek-v3p2",
}

REVERSE_CANONICAL_MODELS: dict[str, str] = {
    canonical: alias for alias, canonical in CANONICAL_MODELS.items()
}

MODEL_DEFAULTS: dict[str, dict[str, int | None]] = {
    "accounts/fireworks/models/deepseek-v3p2": {"max_output_tokens": 64000},
}

SUPPORTED_MODELS: set[str] = set(MODEL_DEFAULTS.keys()) | set(CANONICAL_MODELS.keys())

PRICE_SCHEDULES_USD_PER_MILLION: dict[str, dict[str, float | None]] = {
    "accounts/fireworks/models/deepseek-v3p2": {
        "input": 0.56,
        "input_cached": 0.28,
        "output": 1.68,
    }
}

MODEL_ALIASES: dict[str, str] = {
    "accounts/fireworks/models/deepseek-v3p2": "DeepSeek V3.2",
    "deepseek-v3p2": "DeepSeek V3.2",
}

MODEL_PROVIDERS: dict[str, str] = {
    "accounts/fireworks/models/deepseek-v3p2": "deepseek",
}

PROVIDER_ALIASES: dict[str, str] = {
    "deepseek": "DeepSeek AI (via Fireworks)",
    "fireworks": "Fireworks",
}


@dataclass(frozen=True)
class FireworksResponse:
    payload: dict[str, Any]
    output_text: str


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
    return False


def supports_model(model: str) -> bool:
    return model in SUPPORTED_MODELS


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
    model_id = resolve_model(model)
    if max_output_tokens is None:
        defaults = MODEL_DEFAULTS.get(model_id, {})
        max_output_tokens = defaults.get("max_output_tokens")
    return build_openai_response_request(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model_id,
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


def extract_usage_breakdown(payload: dict[str, Any]) -> TokenBreakdown | None:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    return TokenBreakdown(
        input_tokens=prompt_tokens if isinstance(prompt_tokens, int) else None,
        reasoning_tokens=None,
        output_tokens=completion_tokens if isinstance(completion_tokens, int) else None,
    )


def calculate_cost_breakdown(payload: dict[str, Any], *, model: str) -> CostBreakdown | None:
    schedule = price_schedule_for_model(resolve_model(model))
    if schedule is None:
        return None
    tokens = extract_usage_breakdown(payload)
    if tokens is None:
        return None
    return compute_cost_breakdown(tokens, schedule, output_includes_reasoning=False)


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
        return send_openai_response_request(
            payload,
            api_key=api_key,
            base_url=base_url,
            timeout_s=timeout_s,
            progress_callback=progress_callback,
            stream_text_callback=stream_text_callback,
            sse_event_path=sse_event_path,
            stream_capture=stream_capture,
        )
    except RuntimeError as exc:
        message = str(exc).replace("OpenAI API", "Fireworks API")
        raise RuntimeError(message) from exc


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
) -> FireworksResponse:
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
    return FireworksResponse(
        payload=response_payload,
        output_text=extract_output_text(response_payload),
    )
