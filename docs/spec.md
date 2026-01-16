# Spec Notes

## Purpose
Build a small, reproducible framework for running philosophy-style LLM evaluations with a
shared system prompt, a puzzle library, and append-only capture of requests and responses
across providers.

## Principles
- Keep specs lightweight; record detailed conventions here, not in README.
- Prefer append-only storage with clear provenance and timestamps.
- Preserve provider payloads verbatim when available; for streaming responses without a final payload, record a reconstructed payload derived from the assembled output text and metadata. Normalize only when it adds clear value (e.g. we don't store SSE events).
- Treat prompts as fixtures; avoid runtime mutation.
- Favor minimal modules and simple data shapes over heavy abstractions.

## Architecture overview
- Prompts are Python modules that define system prompts and puzzles.
- Provider adapters build requests and send them, handling provider quirks locally.
- The runner orchestrates a single puzzle run, records request/response data, and writes
  a readable text artifact.
- Storage is append-only JSONL plus a single text file per response.

## Repository layout
- `prompts/`
  - `system.py` (one paragraph prompt with annotations)
  - `puzzles/` (each puzzle stored as `.py`)
- `providers/` (provider adapters and config handling)
- `src/` (runner, storage, puzzle loading, system prompt loading)
- `scripts/` (CLI entry points)
- `responses/` (append-only JSONL + raw response text, partitioned by provider/model)
- `docs/` (provider notes, schema references, and this spec)

## Data capture requirements
- Log the exact system prompt and puzzle text per request.
- Store provider name, model name, model aliases, parameter settings, and request IDs.
- Store full provider request/response payloads without lossy normalization.
- Persist timing info (request start/end, latency).
- Record price schedules (input/output pricing) to enable cost computation.
- Gemini 3 Pro pricing uses input-length tiers; we assume prompts stay under the 200k input threshold and record a single input/output rate.
- Keep request/response pairs in JSONL for aggregation.
- Generate a readable text file that is only input/output text (one file per response).
- Leave room for analysis workflows (possibly in a separate repo linked by run IDs).

## Prompt and puzzle fixtures
- Each prompt is a `.py` module that exposes a single prompt string plus optional metadata.
- System prompt remains a single paragraph.
- Puzzles must supply non-empty text and stable names.
- Avoid mutating prompts or puzzles at runtime.

## Response storage conventions
- Append-only JSONL files partitioned by provider/model, not by run.
- `responses/<provider>/<model>/requests.jsonl` for outgoing payloads.
- `responses/<provider>/<model>/responses.jsonl` for full provider responses plus metadata.
- `responses/<provider>/<model>/texts/` for raw response text files (one per response).
- `run_id` is a correlation ID stored inside each JSONL record; use it for batch lookup.
- Text filenames: `{special_settings}-{puzzle_name}-v{puzzle_version}-{timestamp}.txt` (UTC).
- Text file contents are standalone:
  `{puzzle_label}: {full_puzzle_name}`
  `Model: {model_alias_or_snapshot} ({provider_alias_or_name})[, {special_settings}]`
  `Completed: {date in "Mmm dd, yyyy" (UTC)}`

  `---- INPUT ----`
  `{input text, with role labels}`

  `---- {model_alias_or_snapshot}'S OUTPUT ----`
  `{output text}`
- `special_settings` captures non-default parameters (provider-specific if needed).

## JSONL schema
- Top-level keys only: `run_id`, `created_at`, `provider`, `model`, `puzzle_name`,
  `puzzle_version`, `special_settings`.
- `request` holds the full provider request payload as sent.
- `response` holds the full provider response payload as received.
- Optional: `derived` for normalized conveniences (tokens, cost, price schedule).

## Streaming behavior
- Prefer streaming for long outputs to avoid connection dropouts.
- Streamed deltas are used only to assemble output text.
- Responses store only the completed provider payload (no SSE events).
- Provider payloads should not include adapter-only helper fields (e.g. Gemini `output_text` or `thoughts_text`); keep those in the JSONL output text field or derived metadata.
- For Gemini streaming, reconstructed thought parts stay inside the response payload `candidates[].content.parts` to mirror the provider shape (not stored in `derived`).
- When streaming returns reasoning summary chunks (e.g. OpenAI `response.reasoning_summary_text.delta`), we store a concatenated summary inside the response payload (`output[].type=reasoning`), preferring `*.done` content and falling back to joined deltas when needed; join multiple summary parts with `\n\n\n`.
- If streaming ends without a completed payload, keep the partial text that was received.
- Optional debug mode for OpenAI streaming can write raw SSE event JSONL under `tmp/` and skip request/response storage.

## Provider handling
- Normalize across providers with a thin adapter interface, at providers/{provider}.py
- Keep per-provider quirks isolated to their adapter.
- Provide a dry-run mode that writes request payloads without sending them.
- Default to the highest available reasoning effort per model.
- Request the most detailed reasoning visibility available for the model.
- Omit tool configuration entirely unless tools are required.
- Target providers: OpenAI, Anthropic, Gemini, plus open-source models via Fireworks.
- Provider API syntax lives in provider-specific docs under `docs/providers/`.

## Adding a model to an existing provider
- Use snapshot model names (e.g., `o3-2025-04-16`). If snapshot names not used (e.g. `gemini-2.5-flash`), make a note of that.
- Add model metadata in the provider adapter: defaults (e.g., max output), aliases, pricing, and any capability flags (e.g., reasoning support).
- Add/extend static tests for request assembly defaults and pricing/alias display.
- Update live tests by extending parameterized model lists where behavior matches; add model-specific live tests for divergent behaviors (e.g., rejects reasoning or accepts sampling).
- Keep live tests grouped by behavior and use `-k` to run just the new model’s parameterized case when validating.
- Update provider docs with parameter support (system prompt, temperature/top_p, reasoning, tools, max output constraints); conduct live tests and record results as such.

## Testing guidance
- Use `pytest` for lightweight tests around loaders and request assembly.
- Keep tests small and local; avoid network calls unless explicitly marked live.
- Live tests must be opt-in, cost-labeled, and gated by environment variables.
- Prefer tests that validate expected use/nonuse of: system prompt, temperature, max output
  length, reasoning effort, tool usage (where supported).
- When asserting a parameter is unsupported on a reasoning-capable model, explicitly enable
  reasoning in the request so the test matches default runner behavior.
- Group tests by their purpose
- Parametrize each test, manually add the relevant model name in as part of an array (will be useful as we add more models)

## Progress
- Added a script to run a single puzzle against one OpenAI model and capture responses.
- Unified the single-run script so it routes to a provider based on the model name.
- Added OpenAI request builder support and tests for o3 reasoning/tool parameters.
- Added opt-in live OpenAI tests (marked `live`) for parameter acceptance and errors.
- Live OpenAI call confirmed o3 rejects `temperature`.
- Live OpenAI call confirmed `max_output_tokens` minimum is 16 for o3.
- Added live tests for o3 `top_p` rejection and `max_output_tokens` upper bound.
- Live OpenAI call accepted `max_output_tokens=100001`, upper bound still unknown.
- Added live tests for o3 reasoning effort values and invalid `max_output_tokens`.
- Live OpenAI calls confirmed o3 reasoning effort accepts `low`/`medium`/`high` and
  rejects values that are enabled for other OpenAI models: `none`/`minimal`/`xhigh`.
- Added provider price schedule capture to response-derived metadata.
- Enabled OpenAI streaming response capture with delta assembly for long outputs.
- Added an opt-in live OpenAI streaming test that validates streaming output assembly.
- Streaming runs now store only the completed provider response payload (no SSE events)
  while still capturing streamed text for output.
- Added gpt-4o snapshot model metadata (alias/pricing) and static request tests.
- Added opt-in live OpenAI tests for gpt-4o snapshot basic responses and sampling parameters.
- Relaxed the streaming live test to avoid reasoning parameters so multiple models can run.
- Added a Gemini provider adapter with request capture, a run script, and static/live tests.
- Added Gemini streaming support with reconstructed payload capture.
- Added Gemini 3 Pro preview model support with thinking-config live test.
- Gemini runner now defaults Gemini 3 Pro to high thinking with thought inclusion.
- Gemini streaming payloads now store reconstructed thought/output parts instead of per-chunk parts.
- Gemini responses omit adapter-only `output_text`/`thoughts_text` fields; backfilled existing Gemini JSONL records.
- Added an OpenAI SSE debug toggle to capture raw streaming events without recording requests/responses.
- Added OpenAI gpt-5.2-2025-12-11 model metadata (alias, pricing, defaults) and test coverage.
- Live OpenAI call confirmed gpt-5.2-2025-12-11 rejects `temperature`.
- OpenAI streaming now reconstructs reasoning summaries into the response payload reasoning item.
- Added a live Gemini test to probe whether `temperature` is rejected when `thinking_config` is enabled.

## TODO
- Wire up additional provider adapters after validating the OpenAI run script end-to-end.
- Capture Gemini long-output pricing tiers for cost modeling.
- Capture Gemini 3 Pro preview pricing for cost modeling.
- Run live OpenAI tests for gpt-5.2-2025-12-11 to confirm `top_p` support and reasoning summary behavior.
- Run live Gemini tests for gemini-3-pro-preview to confirm whether `temperature` is rejected when `thinking_config` is enabled.
