# OpenAI Provider Notes

- API: Responses (`POST https://api.openai.com/v1/responses`)
- Auth: `OPENAI_API_KEY`
- Docs: https://platform.openai.com/docs/api-reference/responses (blocked in this environment by Cloudflare)
  - Local: pasted in
- SDK: openai-python `OpenAI()` client with Responses API, supports custom `base_url` (or `OPENAI_BASE_URL`) for OpenAI-compatible providers.

## Models
- Note that not all models appear consistently in the pricing on the docs
  - e.g. gpt-4o is listed on the pricing page as: gpt-4o ($2.50/$10), and gpt-4o-2024-05-13 ($5/$15). So there's clearly a difference due to price. The unmarked one probably points to gpt-4o-2024-11-20, and there's another one in the pricing that's only listed under fine-tuning, gpt-4o-2024-08-16 (which in the Models part is surprisingly marked as 'default')
- 5.2
- 5.1
- 5
- 5 mini
- 5 nano
- 5.2 Codex
- 5.1 Codex
- 5.1 Codex Max
- 5 Codex
- 5.2 Pro
- 5 Pro
- o3 pro
- o3
- o4 mini
- 4.1 nano
- o1 pro
- 4.5 preview (deprecated)
- o3 mini
- o1
- o1 mini (deprecated)
- o1 preview (deprecated)
- 4o
- 4o mini
- 4 turbo
- 5.2
- babbage 002 (deprecated)
- 4o
- 5.1 Codex mini
- 3.5 turbo
  - gpt-3.5-turbo-instruct (shutdown 9/28/26)
  - gpt-3.5-turbo-1106 (shutdown 9/28/26)
- 4
  - gpt-4-1106-preview (shutdown 3/26/26)
  - gpt-4-0613
  - gpt-4-0314 (shutdown 3/26/26)
  - gpt-4-0125 (i.e. 4 turbo preview (?) - deprecated, shuts down 3/26/26)
- oss-120b
- oss-20b

(excludes 'chat' models like 5.2 Chat, and various other TTS, image gen, realtime audio, embedding etc. models)

## Model parameter availability
- Source: pasted Responses API docs below plus live call results.
- Constraints: `max_output_tokens` is required for any call, and must be >= 16.
- o3-2025-04-16:
  - Supported: `system`/`user` input items, `max_output_tokens`, `reasoning` (`effort`, `summary`), `tools`, `tool_choice`, `seed`, `stream`, `stream_options` (per docs and live-verified).
  - Not supported: `temperature`, `top_p` (live call returns 400 unsupported parameter).
  - Max output upper bound is not reliably enforced in live calls (100001 and 1000001 both succeeded); trust docs for the effective limit.
  - Reasoning effort values:
    - Live: `low`, `medium`, `high` accepted; others (e.g. `ultra`) rejected - 400 unsupported.
  - Error shape observed for invalid `max_output_tokens` (below minimum): HTTP 400, `invalid_request_error`, `param: max_output_tokens`, `code: integer_below_min_value`.
- Debugging note: a `--debug-sse` run records raw SSE event JSONL (event objects such as `response.completed` and `response.reasoning_text.done`) under `tmp/` without writing to request/response JSONL storage.
- Streaming note: when SSE includes reasoning summary deltas (e.g. `response.reasoning_summary_text.delta`), the runner stores a concatenated summary inside the response payload reasoning item (`output[].type=reasoning`), preferring `*.done` content and falling back to joined deltas, using `\n\n\n` between parts.
- gpt-5.2-2025-12-11:
  - Supported: `system`/`user` input items, `max_output_tokens`, `reasoning` (`effort`, `summary`), `tools`, `tool_choice`, `seed`, `stream`, `stream_options`.
  - Not supported: `temperature` (live call returns 400 unsupported parameter).
  - Unverified: `top_p`.
  - Defaults: `max_output_tokens=128000`.
- gpt-4o-2024-05-13:
  - Supported: `system`/`user` input items, `max_output_tokens`, `temperature`, `top_p` (docs and live confirmation).
  - Not supported: `reasoning` (docs and live confirmation).
  - Constraints: `max_output_tokens` upper bound expected 64k output (per docs; unconfirmed).
- gpt-4-0613:
  - Supported: `system`/`user` input items, `max_output_tokens`, `temperature`, `top_p`, `tools` (expected based on model generation).
  - Not supported: `reasoning` (predates reasoning models).
  - Constraints: `max_output_tokens=8192`.
- TODO: determine if `max_output_tokens` ever outputs an error for being too high; if so, what is the error point for o3 (and how does it relate to the 'true' max tokens, which are recorded as 100k by OAI).

## Reasoning effort defaults (docs excerpt)
- Supported values: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`.
- gpt-5.1 defaults to `none` (no reasoning). Supported values for gpt-5.1: `none`, `low`, `medium`, `high`. Tool calls supported for all reasoning values in gpt-5.1.
- All models before gpt-5.1 default to `medium` reasoning effort, and do not support `none`.
- gpt-5-pro defaults to (and only supports) `high` reasoning effort.
- `xhigh` is supported for all models after gpt-5.1-codex-max.

## Pricing schedule
- Prices are tracked per million tokens for input/output only (other tiers not yet modeled).
- o3-2025-04-16: input $2.00 / output $8.00 per million tokens.
- gpt-4o-2024-05-13: input $2.50 / output $10.00 per million tokens.
- gpt-5.2-2025-12-11: input $1.75 / output $14.00 per million tokens.
- gpt-4-0613: input $30.00 / output $60.00 per million tokens.
