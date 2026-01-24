# Grok Provider Notes

- NOTE: Grok usage appears to include a large hidden prompt prefix that is reported as part of
  `prompt_tokens_details.text_tokens` and mostly shows up as `cached_tokens` (650 for no-system-prompt, 150
  when there is a system prompt). This inflates prompt token counts beyond the visible text.
  We do not yet model cached-token pricing; current cost estimates will overstate input cost.

- API: Chat Completions (`POST https://api.x.ai/v1/chat/completions`)
- Auth: `XAI_API_KEY`
- Docs: local copies in `docs/providers/grok-docs-reasoning.md` and `docs/providers/grok-docs-streaming.md` (remote docs are JS-rendered)
  - Underspecified: `max_tokens` (not documented and seems to be not respected)
- Timeout: docs recommend extending timeouts for reasoning models; adapter defaults to 3600s.

## Models
- grok-4-1-fast-reasoning (Grok 4.1 Fast Reasoning)
- grok-3 (Grok 3)

## Model parameter availability
- Source: local xAI docs in repo (reasoning + streaming).
- grok-4-1-fast-reasoning:
  - Supported: `messages` with `system` and `user` roles, `stream` (SSE).
  - Supported: `temperature` (live-verified).
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
  - Supported: `messages` with `system` and `user` roles, `temperature`, `stream` (SSE).
  - Max output tokens: 16,384 (per Reddit experiments; unverified).
  - Reasoning: not a reasoning model.

## Streaming payload shape
- SSE chunks look like `chat.completion.chunk` objects with `choices[].delta.content` and a terminating `data: [DONE]` event (per local streaming guide).
- The adapter reconstructs a final `chat.completion`-like payload from stream deltas when no final payload is delivered.

## Pricing schedule (draft)
- grok-4-1-fast-reasoning: input $0.20 / output $0.50 per million tokens.
- grok-3: input $3.00 / output $15.00 per million tokens.

## TODO
- Live-verify supported parameters and error cases once xAI outage clears:
  - System prompt acceptance.
  - Rejection of `presencePenalty`, `frequencyPenalty`, `stop`, and `reasoning_effort`.
  - Whether `max_tokens`, `temperature`, and `top_p` are accepted on grok-4-1-fast-reasoning.
  - Confirm grok-3 temperature acceptance and grok-4.1 temperature rejection in live tests.
  - Stream reconstruction correctness and usage payload shape.
