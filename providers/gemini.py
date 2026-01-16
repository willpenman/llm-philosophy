"""Gemini API adapter via the google-genai SDK."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Callable


MODEL_ALIASES: dict[str, str] = {
    "gemini-2.0-flash-lite-001": "Gemini 2.0 Flash Lite",
    "gemini-3-pro-preview": "Gemini 3 Pro Preview",
}

SUPPORTED_MODELS: set[str] = {
    "gemini-2.0-flash-lite-001",
    "gemini-3-pro-preview",
}

PRICE_SCHEDULES_USD_PER_MILLION: dict[str, dict[str, float | None]] = {
    "gemini-2.0-flash-lite-001": {"input": 0.075, "output": 0.30},
}

PROVIDER_ALIASES: dict[str, str] = {
    "gemini": "Gemini",
}

REASONING_MODELS: set[str] = {"gemini-3-pro-preview"}


@dataclass(frozen=True)
class GeminiResponse:
    payload: dict[str, Any]
    output_text: str


def require_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing GEMINI_API_KEY or GOOGLE_API_KEY for Gemini API access")
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


def build_generate_content_request(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    config: dict[str, Any] = {"system_instruction": system_prompt}
    if max_output_tokens is not None:
        config["max_output_tokens"] = max_output_tokens
    if temperature is not None:
        config["temperature"] = temperature
    if top_p is not None:
        config["top_p"] = top_p
    if top_k is not None:
        config["top_k"] = top_k
    if tools:
        config["tools"] = tools

    return {
        "model": model,
        "contents": user_prompt,
        "config": config,
    }


def _serialize_response(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")
    if hasattr(response, "dict"):
        return response.dict()
    if hasattr(response, "json"):
        try:
            return json.loads(response.json())
        except (TypeError, json.JSONDecodeError):
            return {"raw": response.json()}
    return {"raw": str(response)}


def extract_output_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return ""
    chunks: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "".join(chunks)


def send_generate_content_request(
    payload: dict[str, Any],
    *,
    api_key: str | None = None,
    stream: bool | None = None,
    stream_text_callback: Callable[[str], None] | None = None,
) -> GeminiResponse:
    from google import genai
    from google.genai import errors

    try:
        client_params: dict[str, Any] = {}
        if api_key is not None:
            client_params["api_key"] = api_key
        with genai.Client(**client_params) as client:
            if stream:
                chunks: list[str] = []
                last_payload: dict[str, Any] | None = None
                for chunk in client.models.generate_content_stream(
                    model=payload["model"],
                    contents=payload["contents"],
                    config=payload.get("config"),
                ):
                    chunk_text = getattr(chunk, "text", "")
                    if chunk_text:
                        chunks.append(chunk_text)
                        if stream_text_callback is not None:
                            stream_text_callback(chunk_text)
                    last_payload = _serialize_response(chunk)
                output_text = "".join(chunks)
                response_payload = last_payload or {}
                response_payload["stream"] = True
                response_payload["output_text"] = output_text
                return GeminiResponse(payload=response_payload, output_text=output_text)

            response = client.models.generate_content(
                model=payload["model"],
                contents=payload["contents"],
                config=payload.get("config"),
            )
    except errors.APIError as exc:
        raise RuntimeError(f"Gemini API error {exc.code}: {exc.message}") from exc

    response_payload = _serialize_response(response)
    output_text = getattr(response, "text", "")
    if not isinstance(output_text, str) or not output_text:
        output_text = extract_output_text(response_payload)
    return GeminiResponse(payload=response_payload, output_text=output_text)


def create_response(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    tools: list[dict[str, Any]] | None = None,
    stream: bool | None = None,
    api_key: str | None = None,
) -> GeminiResponse:
    payload = build_generate_content_request(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        tools=tools,
    )
    return send_generate_content_request(
        payload,
        api_key=api_key or require_api_key(),
        stream=stream,
    )
