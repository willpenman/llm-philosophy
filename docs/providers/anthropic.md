# Anthropic Provider Notes

- API: Messages (`POST https://api.anthropic.com/v1/messages`)
- Auth: `ANTHROPIC_API_KEY`
- Headers: `anthropic-version: 2023-06-01` (required)
- Docs source: `docs/providers/anthropic-docs-extended-thinking.md`, `anthropic-docs-streaming.md`,
  `anthropic-docs-effort.md`, `anthropic-docs-pricing.md`

## Models
- Claude Opus 4.5 (`claude-opus-4-5-20251101`) (first supported here)
- Extended thinking docs list: Claude Sonnet 4.5/4/3.7, Claude Haiku 4.5, Claude Opus 4.5/4.1/4

## Model parameter availability
- `system`: supported, accepts an array of text blocks (we pass a single text block with the system prompt).
- `messages`: list of role/content items; we use a single user message with string content.
- `max_tokens`: required; `budget_tokens` must be less than `max_tokens` when thinking is enabled.
  - Live test: Opus 4.5 rejects `max_tokens` that exceed the model limit (e.g., 64,001 fails).
- `thinking` (extended thinking):
  - Supported for Claude 4/4.5 models, including Opus 4.5.
  - Use `{"type": "enabled", "budget_tokens": <int>}`.
  - Required for our eval runs; this adapter enables thinking by default for Opus 4.5.
  - `budget_tokens` is required whenever thinking is enabled (default is 20,000 for Opus 4.5).
  - Thinking output is summarized for Claude 4.x; usage billing counts the full thinking tokens.
  - Incompatible with `temperature` and `top_k`; `top_p` is allowed between 0.95 and 1.0.
  - Streaming required when `max_tokens` exceeds 21,333.
- `temperature`, `top_p`, `top_k`: supported generally, but see thinking incompatibilities above.
- `effort` (beta): only Claude Opus 4.5; requires beta header `effort-2025-11-24`
  and `output_config.effort`. `high` is the default and equivalent to omitting the parameter.
  For this eval suite we do nothing because we already want maximum effort.
- Tools: not configured in this adapter unless explicitly added later.

## Streaming payload shape
- SSE event flow: `message_start` -> content blocks (`content_block_start`/`content_block_delta`/`content_block_stop`)
  -> `message_delta` (usage + stop reason) -> `message_stop`.
- Text content arrives via `content_block_delta` events with `delta.type="text_delta"`.
- Thinking content arrives via `delta.type="thinking_delta"` and a `signature_delta` before block stop.
- `usage` in streaming events is cumulative.

## Usage fields
- `usage.input_tokens`, `usage.output_tokens` are provided in message payloads.
- Prompt caching adds `cache_creation_input_tokens` and `cache_read_input_tokens` fields.

## Pricing schedule (draft)
- Prices tracked per million tokens for base input/output only.
- Claude Opus 4.5: input $5.00 / output $25.00 per million tokens.
- Complete cost modeling sums `input_tokens` + cache read/write tokens and applies the base input rate
  (cache multipliers are not modeled yet), we use a simplified version with just input tokens.
