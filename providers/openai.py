"""OpenAI Responses API adapter."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Callable, Iterator
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://api.openai.com/v1/responses"

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
        raise RuntimeError(f"Failed to parse OpenAI stream event: {data}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Unexpected OpenAI stream event payload: {parsed}")
    return parsed


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
    done_texts: dict[int, str],
    delta_chunks: dict[int, list[str]],
) -> list[str]:
    parts: list[str] = []
    for index in sorted(set(done_texts) | set(delta_chunks)):
        done_text = done_texts.get(index)
        if isinstance(done_text, str) and done_text:
            parts.append(done_text)
            continue
        deltas = delta_chunks.get(index)
        if isinstance(deltas, list) and deltas:
            parts.append("".join(deltas))
    return parts


def inject_reasoning_summary_from_stream(
    response_payload: dict[str, Any] | None,
    stream_capture: dict[str, Any] | None,
) -> None:
    if not isinstance(response_payload, dict) or not isinstance(stream_capture, dict):
        return
    done_texts = stream_capture.get("reasoning_summary_done")
    delta_chunks = stream_capture.get("reasoning_summary_deltas")
    if not isinstance(done_texts, dict) or not isinstance(delta_chunks, dict):
        return
    summary_parts = _coalesce_reasoning_summary_parts(
        done_texts=done_texts,
        delta_chunks=delta_chunks,
    )
    if not summary_parts:
        return
    summary_text = "\n\n\n".join(summary_parts)
    outputs = response_payload.get("output")
    if not isinstance(outputs, list):
        return
    for item in outputs:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "reasoning":
            continue
        item["summary"] = [{"type": "summary_text", "text": summary_text}]
        break


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
            if payload.get("stream") is True:
                streamed_chars = 0
                response_payload: dict[str, Any] | None = None
                summary_chunks: dict[int, list[str]] = {}
                summary_done_texts: dict[int, str] = {}
                sse_handle = None
                if sse_event_path is not None:
                    sse_event_path.parent.mkdir(parents=True, exist_ok=True)
                    sse_handle = sse_event_path.open("a", encoding="utf-8")
                try:
                    for event in _iter_sse_events(response):
                        if sse_handle is not None:
                            sse_handle.write(json.dumps(event, ensure_ascii=True))
                            sse_handle.write("\n")
                        if event.get("type") == "response.output_text.delta":
                            delta = event.get("delta")
                            if isinstance(delta, str):
                                streamed_chars += len(delta)
                                if stream_text_callback is not None:
                                    stream_text_callback(delta)
                                if progress_callback is not None:
                                    progress_callback(streamed_chars)
                        elif event.get("type") == "response.reasoning_summary_text.delta":
                            delta = event.get("delta")
                            index = event.get("summary_index")
                            if isinstance(delta, str) and isinstance(index, int):
                                summary_chunks.setdefault(index, []).append(delta)
                        elif event.get("type") == "response.reasoning_summary_part.done":
                            index = event.get("summary_index")
                            part = event.get("part")
                            if isinstance(index, int) and isinstance(part, dict):
                                text = part.get("text")
                                if isinstance(text, str):
                                    summary_done_texts[index] = text
                        elif event.get("type") in {
                            "response.completed",
                            "response.failed",
                        }:
                            response = event.get("response")
                            if isinstance(response, dict):
                                response_payload = response
                finally:
                    if sse_handle is not None:
                        sse_handle.close()
                if stream_capture is not None:
                    stream_capture["reasoning_summary_done"] = summary_done_texts
                    stream_capture["reasoning_summary_deltas"] = summary_chunks
                return response_payload or {}
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI API connection error: {exc}") from exc
    return json.loads(body)


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
