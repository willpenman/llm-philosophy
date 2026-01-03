# Spec Notes

## Repo shape (draft)
- `prompts/`
  - `system.py` (one paragraph prompt with annotations)
  - `puzzles/` (each puzzle as a few paragraphs, stored as `.py`)
- `responses/` (append-only JSONL + raw response text, partitioned by provider/model)
- `providers/` (provider adapters and config handling)
- `scripts/` (CLI entry points)
- `src/` (core framework code)
- `docs/` (provider notes, TODOs, and schema references)

## Data capture requirements
- Log the exact system prompt and puzzle text per request.
- Store all metadata - provider name, model name, temperature, max tokens (always set to model max), stop sequences, seed, thinking tokens, request IDs.
- Store full provider request/response blobs without lossy normalization.
- Record model cost structure (input/output pricing) to compute per-run cost.
- Persist timing info (request start/end, latency).
- Keep request/response pairs in JSONL for aggregation.
- Generate a readable format that is just the raw response text (one file per response).
- Leave room for analysis workflows (possibly in a separate repo linked by run IDs).

## Prompt module expectations
- Each prompt is a `.py` module that exposes a single prompt string plus optional metadata.
- Treat prompts as fixtures; avoid runtime mutation.
- Keep the system prompt one paragraph.

## Response storage conventions (draft)
- Append-only JSONL files partitioned by provider/model, not by run.
- `responses/<provider>/<model>/requests.jsonl` for outgoing payloads.
- `responses/<provider>/<model>/responses.jsonl` for structured outputs and metadata.
- `responses/<provider>/<model>/texts/` for raw response text files (one per response).
- `run_id` is a correlation ID stored inside each JSONL record; use it for batch lookup.
- Optional: `responses/runs.jsonl` to store per-run metadata (puzzle set, models, timestamp).
- Text filenames: `{special_settings}-{puzzle_name}-v{puzzle_version}-completion{n}.txt`.
- Text file contents should be standalone:
  `{full_puzzle_name}`
  `{model} ({provider}), {special_settings}`
  `{date}`

  `Input:`
  `{input text, including labels of "System", "User", or provider-specific roles}`

  `Output:`
  `{output text}`

  `{response text}`
- `special_settings` covers non-default parameters (e.g., temperature sweeps) and may be provider-specific.

## JSONL schema sketch (draft)
- Top-level keys only: `run_id`, `created_at`, `provider`, `model`, `puzzle_name`, `puzzle_version`, `completion_number`, `special_settings`.
- `request` holds the full provider request payload as sent.
- `response` holds the full provider response payload as received.
- Optional: `derived` for normalized conveniences (tokens, cost) if computed.

## Provider handling
- Normalize across providers with a thin adapter interface.
- Keep per-provider quirks isolated to their adapter.
- Avoid hardcoding credentials; use environment variables.
- Provide a dry-run mode that writes the request payloads without sending them.
- Target providers: OpenAI, Anthropic, Gemini, plus open-source models via Fireworks.
- TODO: include links to each provider's dev docs.
- Future: enable synchronous calls to support fast "run all models for this puzzle" and "run all puzzles for this model."
