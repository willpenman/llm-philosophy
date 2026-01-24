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
- `README.md`
- `prompts/`
  - `system.py` (one paragraph prompt with annotations)
  - `puzzles/` (each puzzle stored as `.py`)
- `src/providers/` (provider adapters and config handling)
- `src/` (runner, storage, puzzle loading, system prompt loading)
- `scripts/` (CLI entry points)
- `responses/` (append-only JSONL + raw response text, partitioned by provider/model)
- `docs/` (provider notes, schema references, and this spec)
- `tests/` (static and live tests per provider, additional tests per feature eg cost calculation)
- `tmp/` (output directory for temporary files, eg sse dumps)

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
- Normalize across providers with a thin adapter interface, at src/providers/{provider}.py
- Keep per-provider quirks isolated to their adapter.
- Provide a dry-run mode that writes request payloads without sending them.
- Default to the highest available reasoning effort per model.
- Request the most detailed reasoning visibility available for the model.
- Omit tool configuration entirely unless tools are required.
- Target providers: OpenAI, Anthropic, Gemini, plus open-source models via Fireworks.
- Provider API syntax lives in provider-specific docs under `docs/providers/`.

## Adding a new provider (best practices + coverage)
- Capture provider docs before coding: auth env var, endpoint/SDK, minimal request example.
- Define adapter behavior: system prompt mapping, reasoning/thinking config, sampling params,
  max output, tool config omission defaults, and streaming strategy.
- Preserve raw payloads: store provider request/response exactly as sent/received; avoid
  adapter-only fields in payloads (keep those in derived metadata or text artifacts).
- Streaming: assemble output text from deltas, and if the provider doesn't return a final
  payload, reconstruct a payload that mirrors the provider's normal shape. Provide --debug-sse option to dump to /tmp
- Reasoning visibility: request the most detailed reasoning summary allowed by the model,
  and document any constraints (e.g., required max output, unsupported sampling).
- Model metadata: add snapshot model names, aliases, pricing schedule, defaults, and any
  capability flags (reasoning, sampling, tools) to the adapter.
- Pricing: note any tiered pricing rules and the assumption we use for cost modeling.
- Provider docs must record:
  - Model list (with stable vs preview notes).
  - Parameter availability per model (system prompt, temperature/top_p/top_k, max output,
    reasoning/thinking, tools), plus defaults and known limits.
  - Streaming payload shape and any reconstruction rules.
  - Live-verified behaviors (accept/reject cases) and gaps to test.
- Tests to add:
  - Static request assembly tests for defaults and parameter mapping.
  - Static pricing/alias tests.
  - Live tests (opt-in) for parameter acceptance/rejection, reasoning, and streaming capture.
  - Structure tests with parametrize and the model name(s) directly, e.g. `@pytest.mark.parametrize("model", ["gemini-2.0-flash-lite-001", "gemini-3-pro-preview"])`
  - Ensure tests cover system prompt, temperature, max output length, reasoning/thinking,
    and tools where supported.

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
- OpenAI adapter now uses the openai-python SDK for Responses (supports custom base_url).
- Added a live Gemini test to probe whether `temperature` is rejected when `thinking_config` is enabled.
- Gemini runs now label non-default sampling params (temperature/top_p/top_k) in `special_settings` when not explicitly set.
- Documented provider onboarding best practices and required coverage in the spec.
- Added provider-specific usage/cost extraction helpers and richer run summaries with token usage, cost formatting, and completion links.
- Added an Anthropic Messages adapter with Opus 4.5 defaults, streaming reconstruction, and usage/cost helpers.
- Added Anthropic request assembly tests and wired Anthropic into the run/list scripts.
- Added opt-in live Anthropic tests for system prompt acceptance and temperature+thinking rejection.
- Added Claude Haiku 3 model support plus a live test that thinking is rejected.
- Moved provider adapters under `src/providers` and updated scripts to run as modules without `sys.path` edits.
- Added a Grok provider adapter (Chat Completions), request/stream reconstruction, and static request/cost tests.
- Documented Grok usage shape and aligned Grok usage extraction/tests with docs.
- Flagged Grok hidden cached tokens in provider notes; pricing still overestimates input until cached rates are modeled.
- Added Grok 3 model metadata, pricing, and live tests for temperature acceptance.
- Added a general --debug-sse flag to capture streaming events for OpenAI, Grok, Gemini, and Anthropic.
- Grok ONLY now defaults to non-streaming to retain usage stats; added --streaming override for all providers.

## TODO
 - Wire up the Fireworks provider adapter.
