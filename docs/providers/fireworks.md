# Fireworks Provider Notes

- API: Chat Completions via Fireworks Python SDK (`fireworks-ai`).
- Auth: `FIREWORKS_API_KEY`
- Docs: https://docs.fireworks.ai/tools-sdks/python-sdk
- Serverless only: this adapter only targets the serverless option; on-demand/dedicated are out of scope.

## Why the Fireworks SDK (not OpenAI Responses API)

We originally used OpenAI's Responses SDK pointed at Fireworks' compatible endpoint. However, **Fireworks does not expose reasoning content through their Responses API**—the `reasoning_effort` parameter is silently ignored.

To access `reasoning_content` for DeepSeek V3.2 and other reasoning models, we must use:
- The native **Fireworks Python SDK** (`pip install --pre fireworks-ai`)
- The **Chat Completions API** (not Responses)

Key finding: Even though Fireworks docs say DeepSeek V3.2 has "default reasoning on", you must explicitly pass `reasoning_effort` (any value except 'none') to get `reasoning_content` populated in the response.

## Provider identity

- Fireworks is the API platform, but we store runs under each model maker when available.
- Example: DeepSeek models are stored under provider `deepseek` (displayed as "DeepSeek AI (via Fireworks)").

## Models

### deepseek-v3p2 (DeepSeek V3.2)
- Canonical ID: `accounts/fireworks/models/deepseek-v3p2`
- Context length: 160k tokens (model page).
- Pricing (serverless): $0.56 / 1M input, $0.28 / 1M cached input, $1.68 / 1M output.
- Max output tokens: 64k (DeepSeek's own description, default is 32k).
- Reasoning: Yes. Must use `reasoning_effort` parameter; content appears in `message.reasoning_content`.

### deepseek-v3-0324 (DeepSeek V3 Update 1)
- Canonical ID: `accounts/fireworks/models/deepseek-v3-0324`
- Pricing (serverless): $0.90 / 1M input, $0.45 / 1M cached input, $0.90 / 1M output.
- Max output tokens: 30k (per model configuration; unverified).
- Reasoning: assumed not supported (unverified).

### qwen3-vl-235b-thinking (Qwen3-VL 235B Thinking)
- Canonical ID: `accounts/fireworks/models/qwen3-vl-235b-a22b-thinking`
- Pricing (serverless): $0.22 / 1M input, no cached pricing, $0.88 / 1M output.
- Max output tokens: 38912 (per model configuration).
- Reasoning: Yes. Must use `reasoning_effort` parameter.

### qwen2p5-vl-32b (Qwen2.5-VL 32B)
- Canonical ID: `accounts/fireworks/models/qwen2p5-vl-32b-instruct`
- Pricing (serverless): $0.90 / 1M input, $0.45 / 1M cached input, $0.90 / 1M output.
- Max output tokens: 128000 (per model configuration).
- Reasoning: No.

### kimi-k2p5 (Kimi K2.5)
- Canonical ID: `accounts/fireworks/models/kimi-k2p5`
- Provider: Moonshot AI
- Pricing (serverless): $0.60 / 1M input, $0.10 / 1M cached input, $3.00 / 1M output.
- Max output tokens: 250000.
- Reasoning: Yes. Must use `reasoning_effort` parameter.

### kimi-k2-instruct-0905 (Kimi K2)
- Canonical ID: `accounts/fireworks/models/kimi-k2-instruct-0905`
- Provider: Moonshot AI
- Pricing (serverless): $0.60 / 1M input, $0.30 / 1M cached input, $2.50 / 1M output.
- Max output tokens: 250000.
- Reasoning: Yes. Must use `reasoning_effort` parameter.

### llama-v3p3-70b-instruct (Llama 3.3 70B)
- Canonical ID: `accounts/fireworks/models/llama-v3p3-70b-instruct`
- Provider: Meta
- Pricing (serverless): $0.90 / 1M input, $0.45 / 1M cached input, $0.90 / 1M output.
- Max output tokens: 8192.
- Reasoning: No.

## Adding a new model

1. Add the model to `CANONICAL_MODELS` in `src/providers/fireworks.py` (alias → canonical ID).
2. Add defaults to `MODEL_DEFAULTS` (at minimum `max_output_tokens`).
3. Add pricing to `PRICE_SCHEDULES_USD_PER_MILLION`.
4. Add display name to `MODEL_ALIASES`.
5. Add provider mapping to `MODEL_PROVIDERS` (e.g., `"deepseek"` for DeepSeek models).
6. If it's a reasoning model, add to `REASONING_MODELS` set.

## Model parameter availability

- DeepSeek V3.2 (via Fireworks Chat Completions):
  - Supported: `messages`, `max_tokens`, `temperature`, `top_p`, `reasoning_effort`, `stream`
  - Reasoning effort: `"low"`, `"medium"`, `"high"`, or `"none"` to disable. For DeepSeek, any non-'none' value enables reasoning output (effort levels have no additional effect).
  - Unsupported: `top_k` (not part of Chat Completions schema), `seed` (not verified)
- DeepSeek V3 Update 1 (via Fireworks Chat Completions):
  - Assumed: `messages`, `max_tokens`, `temperature`, `top_p`, `stream` (unverified).
  - Reasoning effort: not supported (assumed; verify with live tests).
- Qwen3-VL 235B Thinking (via Fireworks Chat Completions):
  - Supported: `messages`, `max_tokens`, `temperature`, `top_p`, `reasoning_effort`, `stream`
- Qwen2.5-VL 32B (via Fireworks Chat Completions):
  - Supported: `messages`, `max_tokens`, `temperature`, `top_p`, `stream`
  - Reasoning effort: not supported.
- Kimi K2.5 (via Fireworks Chat Completions):
  - Supported: `messages`, `max_tokens`, `temperature`, `top_p`, `reasoning_effort`, `stream`
- Kimi K2 (via Fireworks Chat Completions):
  - Supported: `messages`, `max_tokens`, `temperature`, `top_p`, `reasoning_effort`, `stream`
- Llama 3.3 70B (via Fireworks Chat Completions):
  - Supported: `messages`, `max_tokens`, `temperature`, `top_p`, `stream`
  - Reasoning effort: not supported.

## Response structure

Chat Completions responses include:
- `choices[0].message.content` - main output text
- `choices[0].message.reasoning_content` - reasoning/thinking text (when `reasoning_effort` is set)
- `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`

The `reasoning_content` is stored directly in the response payload, following the same pattern as Anthropic's thinking blocks. Conceptually, this is because we are reconstructing the response; we use the `derived` part of the record for metadata not in the response itself, such as cost structure.

## Streaming

- Streaming uses SSE with Chat Completions chunk format.
- Reasoning content streams via `delta.reasoning_content` before `delta.content`.
- Raw events can be captured with `--debug-sse`.
