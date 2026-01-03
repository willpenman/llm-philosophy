"""OpenAI Responses API adapter."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://api.openai.com/v1/responses"

MODEL_DEFAULTS: dict[str, dict[str, int | None]] = {
    "o3-2025-04-16": {"max_output_tokens": 100000},
}


@dataclass(frozen=True)
class OpenAIResponse:
    payload: dict[str, Any]
    output_text: str


def require_api_key(env_var: str = "OPENAI_API_KEY") -> str:
    api_key = os.getenv(env_var)
    if not api_key:
        raise EnvironmentError(f"Missing {env_var} for OpenAI API access")
    return api_key


def _content_item(text: str) -> dict[str, str]:
    return {"type": "text", "text": text}


def build_response_request(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_output_tokens: int | None,
    temperature: float | None = None,
    seed: int | None = None,
    metadata: dict[str, Any] | None = None,
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
    if seed is not None:
        payload["seed"] = seed
    if metadata:
        payload["metadata"] = metadata
    return payload


def send_response_request(
    payload: dict[str, Any],
    *,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout_s: float = 60,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI API connection error: {exc}") from exc
    return json.loads(body)


def extract_output_text(payload: dict[str, Any]) -> str:
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
    seed: int | None = None,
    metadata: dict[str, Any] | None = None,
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
        seed=seed,
        metadata=metadata,
    )
    response_payload = send_response_request(
        payload,
        api_key=api_key or require_api_key(),
        base_url=base_url,
        timeout_s=timeout_s,
    )
    return OpenAIResponse(
        payload=response_payload,
        output_text=extract_output_text(response_payload),
    )
