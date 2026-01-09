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
- Pricing can be multi-tiered by modality, service tier, or output length (e.g., Gemini long-output pricing); keep room to extend beyond input/output.
- Persist timing info (request start/end, latency).
- Keep request/response pairs in JSONL for aggregation.
- Generate a readable format that is just the raw response text (one file per response).
- Leave room for analysis workflows (possibly in a separate repo linked by run IDs).
- Avoid duplicating `run_id` inside provider payloads unless the API requires it.

## Prompt module expectations
- Each prompt is a `.py` module that exposes a single prompt string plus optional metadata.
- Treat prompts as fixtures; avoid runtime mutation.
- Keep the system prompt one paragraph.

## Testing notes (draft)
- Use `pytest` for lightweight smoke tests around loaders and fixtures.
- Keep tests small and local; avoid network calls and provider dependencies.
- Prefer tests that validate prompt/puzzle invariants (non-empty text, stable names).

## Puzzle loader validation (draft)
- `PUZZLE_TEXT` is required and must be a non-empty string.
- `PUZZLE_NAME` defaults to the filename stem; when provided, it must be a non-empty string.
- `PUZZLE_TITLE` and `PUZZLE_VERSION` are optional strings.
- `PUZZLE_METADATA` is optional; when provided, it must be a dict.

## Response storage conventions (draft)
- Append-only JSONL files partitioned by provider/model, not by run.
- `responses/<provider>/<model>/requests.jsonl` for outgoing payloads.
- `responses/<provider>/<model>/responses.jsonl` for structured outputs and metadata.
- `responses/<provider>/<model>/texts/` for readable response files (one per response, `.md` for GitHub rendering).
- `run_id` is a correlation ID stored inside each JSONL record; use it for batch lookup.
- Optional: `responses/runs.jsonl` to store per-run metadata (puzzle set, models, timestamp).
- Text filenames: `{special_settings}-{puzzle_name}-v{puzzle_version}-{timestamp}.md` (UTC timestamp).
- Text file contents should be standalone:
  `{puzzle_label}: {full_puzzle_name}`
  `Model: {model_alias_or_snapshot} ({provider_alias_or_name})[, {special_settings if not default}]`
  `Completed: {date in "Mmm dd, yyyy" (UTC)}`

  `---- INPUT ----`
  ```text
  `{input text, including labels of "System", "User", or provider-specific roles}`
  ```

  `---- {model_alias_or_snapshot}'S OUTPUT ----`
  ```text
  `{output text}`
  ```
- Rationale: GitHub Markdown collapses single newlines inside paragraphs; wrapping input/output in fenced code blocks preserves the model's original line breaks and spacing.

  `{response text}`
- `special_settings` covers non-default parameters (e.g., temperature sweeps) and may be provider-specific.

## JSONL schema sketch (draft)
- Top-level keys only: `run_id`, `created_at`, `provider`, `model`, `puzzle_name`, `puzzle_version`, `special_settings`.
- `request` holds the full provider request payload as sent.
- `response` holds the full provider response payload as received.
- Optional: `derived` for normalized conveniences (tokens, cost, price schedule) if computed.

## Provider handling
- Normalize across providers with a thin adapter interface.
- Keep per-provider quirks isolated to their adapter.
- Avoid hardcoding credentials; use environment variables.
- Provide a dry-run mode that writes the request payloads without sending them.
- Local dev convenience: `.venv/lib/python3.13/site-packages/llm_philosophy.pth` adds the repo root to `sys.path`. It lives inside `.venv`, so it is local and untracked; revisit if packaging/distribution becomes a priority.
- Always use snapshot model names (e.g., `o3-2025-04-16`) to keep runs reproducible.
- Default to the highest available reasoning effort for each provider (provider-specific parameter names).
- Request the most detailed reasoning visibility available (e.g., `summary: detailed` or full reasoning where supported).
- Omit tool configuration entirely unless tools are required; some providers (OpenAI) report more reliable reasoning summaries when `tools` is absent.
- Since we encourage long outputs, prefer streaming when the provider supports it (e.g., Anthropic guidance); capture partials if needed.
- Target providers: OpenAI, Anthropic, Gemini, plus open-source models via Fireworks.
- OpenAI Responses API docs: https://platform.openai.com/docs/api-reference/responses
- TODO: include links to each provider's dev docs.
- Future: enable synchronous calls to support fast "run all models for this puzzle" and "run all puzzles for this model."

## Progress
- Added a script to run a single puzzle against one OpenAI model and capture responses.
- Added OpenAI request builder support and tests for o3 reasoning/tool parameters.
- Added opt-in live OpenAI tests (marked `live`) for o3 parameter acceptance and error handling.
- Live OpenAI call confirmed o3 rejects `temperature`.
- Live OpenAI call confirmed `max_output_tokens` minimum is 16 for o3.
- Added live tests for o3 `top_p` rejection and `max_output_tokens` upper bound.
- Live OpenAI call accepted `max_output_tokens=100001`, upper bound still unknown.
- Added live tests for o3 reasoning effort values and invalid `max_output_tokens`.
- Live OpenAI calls confirmed o3 reasoning effort accepts `low`/`medium`/`high` and rejects `none`/`minimal`/`xhigh`.
- Added provider price schedule capture to response-derived metadata.

## TODO
- Wire up additional provider adapters after validating the OpenAI run script end-to-end.
- Validate o3 parameter support (reasoning/tool settings) with a live OpenAI call.
- Confirm live test expectations (success + invalid reasoning effort) against actual API behavior.
- Run a live call to verify `reasoning` fields are accepted and inspect returned output.
- Confirm o3 `max_output_tokens` upper bound via live calls with higher values.
- Add additional OpenAI models to live test model list with contrasting parameter support.
- Fill in OpenAI per-model input/output pricing values.
- Capture Gemini long-output pricing tiers when adding Gemini support.
