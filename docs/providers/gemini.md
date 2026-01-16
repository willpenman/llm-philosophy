# Gemini Provider Notes

- SDK: `google-genai` (`from google import genai`)
- Auth: `GEMINI_API_KEY` or `GOOGLE_API_KEY` (Google docs note `GOOGLE_API_KEY` takes precedence)
- Docs: https://ai.google.dev/gemini-api/docs and https://googleapis.github.io/python-genai/ (SDK README + reference)

## Models
- gemini-2.0-flash-lite-001 (stable)
- gemini-3-pro-preview (preview; reasoning/thinking enabled)

## Model parameter availability
- Source: `google-genai` README (generate_content + config examples).
- gemini-2.0-flash-lite-001:
  - Supported in SDK: `system_instruction` (system prompt), `max_output_tokens`,
    `temperature`, `top_p`, `top_k`, `tools` (not yet wired in the adapter).
  - Thinking config: model rejects it in live calls.
  - Live: `max_output_tokens=8193` did not error; upper bound is not enforced.
  - Streaming: adapter uses `generate_content_stream` and reconstructs the
    response payload from the final chunk plus assembled output text.
- gemini-3-pro-preview:
  - Supported: `thinking_config` (`thinking_level`, `thinking_budget`, `include_thoughts`)
    - "Use the thinkingLevel parameter with Gemini 3 models. While thinkingBudget is accepted for backwards compatibility, using it with Gemini 3 Pro may result in suboptimal performance."
    - `thinking_level` can be "LOW" or "HIGH" - (for 3 Flash, there's "minimal", "low", "medium", and "high")
    - If you don't specify a thinking level, Gemini will use the Gemini 3 models' default dynamic thinking level, "high". "You cannot disable thinking for Gemini 3 Pro." 
  - Adapter defaults: `thinking_level="HIGH"` and `include_thoughts=True` when using Gemini 3 Pro.
  - Streaming capture: response payload stores reconstructed thought/output parts (single thought part + single output part) rather than per-chunk streaming parts.
  - Storage note: we do not persist adapter convenience fields like `output_text`/`thoughts_text` in the response payload; the response payload keeps the `candidates[].content.parts` shape as the canonical record.
  - Versions: preview only (`gemini-3-pro-preview`).

## Pricing schedule (draft)
- Prices are tracked per million tokens for input/output only (other tiers not yet modeled).
- gemini-2.0-flash-lite-001: input $0.075 / output $0.30 per million tokens.

## SDK usage reference
```python
from google import genai
from google.genai import types

client = genai.Client(api_key="GEMINI_API_KEY")
response = client.models.generate_content(
    model="gemini-2.0-flash-lite-001",
    contents="Hello",
    config=types.GenerateContentConfig(
        system_instruction="System prompt here.",
        max_output_tokens=128,
        temperature=0.2,
        top_p=0.9,
    ),
)
print(response.text)
```
