# Fireworks Provider Notes

- API: Responses (OpenAI-compatible) via Fireworks serverless.
- Base URL: https://api.fireworks.ai/inference/v1
- Auth: `FIREWORKS_API_KEY`
- Docs: https://docs.fireworks.ai/guides/response-api (pasted locally)
- Serverless only: this adapter only targets the serverless option; on-demand/dedicated are out of scope.

## Provider identity
- Fireworks is the API platform, but we store runs under each model maker when available.
- Example: DeepSeek models are stored under provider `deepseek` (displayed as DeepSeek AI).

## Models
- accounts/fireworks/models/deepseek-v3p2 (DeepSeek V3.2)
  - Context length: 160k tokens (model page).
  - Pricing (serverless): $0.56 / 1M input, $0.28 / 1M cached input, $1.68 / 1M output.
  - Max output tokens: not listed on Fireworks model page; we set a max of 64k from DeepSeek's own website.

## Model parameter availability
- Source: Fireworks Responses API docs + model page.
- DeepSeek V3.2 (via Fireworks Responses):
  - Expected/assumed: `system`/`user` input items, `max_output_tokens`, `temperature`, `top_p`, `tools`, `tool_choice`, `seed`, `stream`, `stream_options` (OpenAI-compatible surface).
  - Unsupported/unknown: `reasoning` (not documented for Fireworks Responses); `top_k` (not part of Responses schema).
  - TODO: live-verify which sampling parameters are accepted and whether any are rejected.

## Usage shape
- Responses include `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens` (docs).

## Streaming
- Streaming uses SSE with OpenAI-style response events. Raw events can be captured with `--debug-sse`.
