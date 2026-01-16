# Gemini Provider Notes

- SDK: `google-genai` (`from google import genai`)
- Auth: `GEMINI_API_KEY` or `GOOGLE_API_KEY` (Google docs note `GOOGLE_API_KEY` takes precedence)
- Docs: https://googleapis.github.io/python-genai/ (SDK README + reference)

## Models
- gemini-2.0-flash-lite-001 (initial target)

## Model parameter availability
- Source: `google-genai` README (generate_content + config examples).
- gemini-2.0-flash-lite-001:
  - Supported in SDK: `system_instruction` (system prompt), `max_output_tokens`,
    `temperature`, `top_p`, `top_k`, `tools` (not yet wired in the adapter).
  - Thinking config: SDK exposes `thinking_config` (`thinking_level`, `thinking_budget`,
    `include_thoughts`), but the model rejects it in live calls.
  - Live: `max_output_tokens=8193` did not error; upper bound is not enforced.
- Streaming: adapter uses `generate_content_stream` and reconstructs the
  response payload from the final chunk plus assembled output text.

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
