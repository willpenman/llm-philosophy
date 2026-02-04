# Grok Provider Notes

- NOTE: Grok usage appears to include a large hidden prompt prefix that is reported as part of
  `prompt_tokens_details.text_tokens` and mostly shows up as `cached_tokens` (650 for no-system-prompt, 150
  when there is a system prompt). This inflates prompt token counts beyond the visible text.
  We do not yet model cached-token pricing; current cost estimates will overstate input cost.
- NOTE: Grok streaming currently omits usage stats in SSE chunks (contra docs). We default to non-streaming
  to retain usage data and since no model has so far pushed to high token outputs. If connections drop, users can rerun with `--streaming true`.
    - Actual SSE chunks (Jan 2026, incl 4.1): `{"id": "881b35e0-6d73-ccd5-74c4-5c7fa318adf0", "object": "chat.completion.chunk", "created": 1769224571, "model": "grok-4-1-fast-reasoning", "choices": [{"index": 0, "delta": {"content": " rebellion"}}], "system_fingerprint": "fp_8c17c6cdd4"} ... {"id": "881b35e0-6d73-ccd5-74c4-5c7fa318adf0", "object": "chat.completion.chunk", "created": 1769224572, "model": "grok-4-1-fast-reasoning", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}], "system_fingerprint": "fp_8c17c6cdd4"}`

- API: Chat Completions (`POST https://api.x.ai/v1/chat/completions`)
- Auth: `XAI_API_KEY`
- Docs: local copies in `docs/providers/grok-docs-reasoning.md` and `docs/providers/grok-docs-streaming.md` (remote docs are JS-rendered)
  - Underspecified: `max_tokens` (not documented and seems to be not respected)
- Timeout: docs recommend extending timeouts for reasoning models; adapter defaults to 3600s.

## Models
- grok-4-1-fast-reasoning (Grok 4.1 Fast Reasoning)
- grok-3 (Grok 3)
- grok-2-vision-1212 (Grok 2)

## Model parameter availability
- Source: local xAI docs in repo (reasoning + streaming).
- grok-4-1-fast-reasoning:
  - Adapter supports: `messages` with `system` and `user` roles, `max_tokens`, `temperature`, `top_p`, `stream` (SSE).
  - Live-verified: system prompt, `temperature`.
  - Max output tokens: 256k (purported; unverified).
  - Not supported on reasoning models: `presencePenalty`, `frequencyPenalty`, `stop` (docs warn these return errors).
  - `top_p` (not documented in local guides; unverified).
  - Not supported: `reasoning_effort` (docs warn it returns an error for grok-4* reasoning models).
  - Reasoning visibility: no `reasoning_content` returned for Grok 4.x; encrypted reasoning only described for the Responses API, not the Chat Completions API.
  - Usage: docs mention `reasoning_tokens` in usage metrics; verify exact field shape live.
  - Usage shape (docs): `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`, plus
    `usage.prompt_tokens_details.{text_tokens,audio_tokens,image_tokens,cached_tokens}` and
    `usage.completion_tokens_details.{reasoning_tokens,audio_tokens,accepted_prediction_tokens,rejected_prediction_tokens}`.
- grok-3:
  - Adapter supports: `messages` with `system` and `user` roles, `max_tokens`, `temperature`, `top_p`, `stream` (SSE).
  - Live-verified: `temperature`.
  - Max output tokens: 16,384 (per Reddit experiments; unverified).
  - Reasoning: not a reasoning model (expects `reasoning_effort` to be rejected; live test added).
- grok-2-vision-1212:
  - Vision-capable model; adapter currently sends text-only requests.
  - Adapter supports: `messages` with `system` and `user` roles, `max_tokens`, `temperature`, `top_p`, `stream` (SSE).
  - Temperature: unverified (live test added).
  - Max output tokens: 131,072 (per xAI pricing sheet; unverified).
  - Reasoning: not a reasoning model (expects `reasoning_effort` to be rejected; live test added).

## Streaming payload shape
- SSE chunks look like `chat.completion.chunk` objects with `choices[].delta.content` and a terminating `data: [DONE]` event (per local streaming guide).
- The adapter reconstructs a final `chat.completion`-like payload from stream deltas when no final payload is delivered.

## Pricing schedule
- grok-4-1-fast-reasoning: input $0.20 / output $0.50 per million tokens.
- grok-3: input $3.00 / output $15.00 per million tokens.
- grok-2-vision-1212: input $2.00 / output $10.00 per million tokens.
