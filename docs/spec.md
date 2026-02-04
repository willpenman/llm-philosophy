# Spec Notes

## Purpose
Build a small, reproducible framework for running philosophy-style LLM evaluations with a
shared system prompt, a puzzle library, and append-only capture of requests and responses
across providers.

## Principles
- Keep specs lightweight; record detailed conventions here, not in README.
- Prefer append-only storage with clear provenance and timestamps.
- Preserve provider payloads verbatim when available; for streaming responses without a final payload, record a reconstructed payload derived from the assembled output text and metadata. Normalize only when it adds clear value (e.g. we don't store SSE events).
- Treat prompts as fixtures; avoid runtime mutation except for appending model-specific
  output-length guidance to the system prompt.
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
- Generate a readable document file that is only input/output text (one file per response).
- Leave room for analysis workflows (possibly in a separate repo linked by run IDs).

## Prompt and puzzle fixtures
- Each prompt is a `.py` module that exposes a single prompt string plus optional metadata.
- System prompt is a single paragraph, with per-max-output-class length enumeration ("about 40,000 words").
- Puzzles must supply non-empty text and stable names.
- Avoid mutating prompts or puzzles at runtime, except for the system prompt's appended
  output-length guidance derived from model max output tokens.

## Response storage conventions
- Append-only JSONL files partitioned by provider/model, not by run.
- `responses/<provider>/<model>/requests.jsonl` for outgoing payloads.
- `responses/<provider>/<model>/responses.jsonl` for full provider responses plus metadata.
- `responses/<provider>/<model>/texts/` for response `.docx` files (one per response).
- `run_id` is a correlation ID stored inside each JSONL record; use it for batch lookup.
- Docx filenames: `{special_settings}-{puzzle_name}-v{puzzle_version}-{timestamp}.docx` (UTC).
- Docx structure mirrors the prior text artifact:
  - Document title: `{full_puzzle_name}`
  - Title paragraph (style `Title`): `{full_puzzle_name}`
  - Centered header lines:
    `{puzzle_label}: {full_puzzle_name} (v{puzzle_version})`
    `LLM: {model_alias_or_snapshot} ({provider_alias_or_name})[, {special_settings}]`
    `Completed: {date in "Mmm dd, yyyy" (UTC)}`
  - Heading 1: `Input given to {model_alias_or_snapshot}`, followed by the full input text (system + user) as-is.
  - Page break; Heading 1: `{model_alias_or_snapshot}'s Output`, followed by the full output text as-is.
  - Page numbers enabled.
- `special_settings` captures non-default parameters (provider-specific if needed).
- If anything changes (e.g. adding price reporting, thought summaries, etc.), use `backfill_docx.py` to apply it to all existing texts.

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
- All open-weights models are run through Fireworks; see below.
- Use snapshot model names (e.g., `o3-2025-04-16`). If snapshot names not available (e.g. `gemini-2.5-flash`), make a note of that.
- Add model metadata in the provider adapter: defaults (e.g., max output), aliases, pricing, and any capability flags (e.g., reasoning support). Ask if not provided.
- Add/extend static tests for request assembly defaults and pricing/alias display. We always assume that a model supports 'system' messages. 
- Update live tests by extending parameterized model lists per parameter, where behavior matches, e.g. 'accepts reasoning' or 'rejects reasoning'
- Keep live tests grouped by behavior (see comments in code). 
- Run live tests, use `-k` to run just the new model's parameterized case when validating, eg `source .venv/bin/activate && RUN_LIVE_OPENAI=1 pytest tests/test_openai_live.py -k gpt-4o-2024-05-13 -m live`, or for a single one, `source .venv/bin/activate && RUN_LIVE_OPENAI=1 pytest tests/test_openai_live.py -k "accepts_tools_live and gpt-4o-2024-05-13" -m live`
- Update provider docs with parameter support based on tests (system prompt, temperature/top_p, reasoning, tools, max output constraints). Treat tests as the arbiter of uncertain assumptions (e.g. of parameter support)
- Update model_release_registry and README with our system's support for that model.

### Fireworks-specific (open-weights models)
- Add alias→canonical mapping in `CANONICAL_MODELS` (e.g., `"deepseek-v3p2": "accounts/fireworks/models/deepseek-v3p2"`).
- Add to `MODEL_DEFAULTS`, `PRICE_SCHEDULES_USD_PER_MILLION`, `MODEL_ALIASES`, `MODEL_PROVIDERS`.
- If reasoning model, add to `REASONING_MODELS` set (enables auto `reasoning_effort="hight"`).

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
- Added initial Fireworks Responses adapter (OpenAI-compatible) with DeepSeek V3.2 support, pricing metadata, and request/live tests.
- Migrated Fireworks to native SDK (Chat Completions API) to access `reasoning_content`—Responses API silently ignores `reasoning_effort`.
- Fireworks requires explicit `reasoning_effort` param to populate `reasoning_content` (despite docs saying "default reasoning on").
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
- Added a model-specific output-length guidance sentence that appends to the system prompt at runtime.
- Added .docx response artifacts with centered headers, H1 input/output sections, and page numbers; added a backfill script to convert legacy .txt files.
- Added a model release registry (`docs/model_release_registry.md`) and a README timeline table by year/provider.
- Expanded the model release registry and README timeline with additional Meta, Mistral, and Qwen entries (unsupported).
- Backfilled older Meta/Qwen history and added a 2022 column with ChatGPT to the README timeline.
- Added Moonshot AI (Kimi) entries to the model release registry and README timeline.
- Added a 2026 column and Kimi K2.5 entry to the model release registry and README timeline.
- Updated run summaries to show combined reasoning+output tokens/costs when provider usage omits reasoning token splits.
- Added Grok 2 Vision (`grok-2-vision-1212`) model metadata, pricing, and tests.
- Added Grok live tests to verify non-reasoning models reject `reasoning_effort`.
- Updated model release registry + README timeline to mark deprecated lines based on Fireworks serverless availability and xAI console status.
- Added DeepSeek V3 Update 1 (`deepseek-v3-0324`) model metadata in the Fireworks adapter, plus request/live test coverage and documentation updates.

## TODO
- Verify Fireworks Chat Completions parameter support (temperature/top_p) and max output token limits for DeepSeek V3.2.
- Verify Fireworks Chat Completions parameter support (temperature/top_p) and max output token limits for DeepSeek V3 Update 1 (`deepseek-v3-0324`).
- Add live tests for Fireworks reasoning content capture.
- Confirm Grok 2 Vision release date/source and live-verify its parameter support.
