# Spec Notes

## Purpose
Build a small, reproducible framework for running philosophy-style LLM evaluations with a
shared system prompt, a puzzle library, and append-only capture of requests and responses
across providers.

## Principles
- Preserve provider payloads verbatim when available; for streaming responses without a final payload, record a reconstructed payload derived from the assembled output text and metadata. Normalize only when it adds clear value (e.g. we don't store SSE events).
- Treat prompts as fixtures; avoid runtime mutation except for appending model-specific output-length guidance to the system prompt derived from model max output tokens.. - Each prompt is a `.py` module that exposes a single prompt string plus optional metadata. System prompt is a single paragraph, with per-max-output-class length enumeration ("about 40,000 words"). Puzzles must supply non-empty text and stable names.
- Avoid mutating prompts or puzzles at runtime, except for the system prompt's appended

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
- `baselines/` (baseline prompts and responses for calibration)
  - `prompts.py` (baseline prompt definitions)
  - `responses/` (append-only JSONL, partitioned by provider/model)
- `analysis/` (embedding-based analysis and visualization)
  - `embeddings.py` (embedding generation and caching)
  - `distances.py` (distance matrix computation and projection)
  - `visualize.py` (plotting utilities)
  - `embeddings/` (cached embedding files as `.npz`)

## Response storage conventions
- Append-only JSONL files partitioned by provider/model, not by run.
  - Top-level keys: `run_id`, `created_at`, `provider`, `model`, `puzzle_name`, `puzzle_version`, `special_settings`.
  - `request` holds the full provider request payload as sent.
  - `response` holds the full provider response payload as received.
  - `derived` for normalized conveniences (tokens, cost, price schedule).
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
    `LLM: {model_display} ({provider_alias_or_name})[, {special_settings}]`
    `Completed by {model_display}: {date in "Mmm dd, yyyy" (UTC)}`
  - Heading 1: `Input given to {model_alias_or_snapshot}`, followed by the full input text (system + user) as-is.
  - Heading 2: `System` and `User` labels
  - Page break; Heading 1: `{model_alias_or_snapshot}'s Output`, followed by the full output text as-is.
  - Page numbers enabled.
- `special_settings` captures non-default parameters (e.g. temperature).
- If anything changes (e.g. adding price reporting, thought summaries, etc.), use `backfill_docx.py` to apply it to all existing texts.


## Streaming behavior
- Prefer streaming for long outputs to avoid connection dropouts.
- Streamed deltas are used only to assemble output text.
- Responses store only the completed provider payload (no SSE events).
- Provider payloads should not include adapter-only helper fields (e.g. Gemini `output_text` or `thoughts_text`); keep those in the JSONL output text field or derived metadata.
- For Gemini streaming, reconstructed thought parts stay inside the response payload `candidates[].content.parts` to mirror the provider shape (not stored in `derived`).
- When streaming returns reasoning summary chunks (e.g. OpenAI `response.reasoning_summary_text.delta`), we store a concatenated summary inside the response payload (`output[].type=reasoning`), preferring `*.done` content and falling back to joined deltas when needed; join multiple summary parts with `\n\n\n`.
- If streaming ends without a completed payload, keep the partial text that was received.
- Optional debug mode for OpenAI streaming can write raw SSE event JSONL under `tmp/` and skip request/response storage.


## Adding a model to an existing provider
0. Examine provider-specific documentation, docs/providers/{provider}.md, e.g. anthropic.md - this carries inter-model insights about how to add models and what particularities they have
1. Add model metadata in the provider adapter (src/providers/{provider}.py): defaults (e.g., max output), aliases, pricing, and any capability flags (e.g., reasoning support). Ask if not provided.
2. Add/extend static tests (tests/test_{provider}_request.py) for request assembly defaults and pricing/alias display. We always assume that a model supports 'system' messages. 
3. Update live tests (tests/test_{provider}_live.py) by extending parameterized model lists per parameter, where behavior matches, e.g. 'accepts reasoning' or 'rejects reasoning'
  - Keep live tests grouped by behavior (see comments in code). 
  - Run live tests, use `-k` to run just the new model's parameterized case when validating, eg `source .venv/bin/activate && RUN_LIVE_OPENAI=1 pytest tests/test_openai_live.py -k gpt-4o-2024-05-13 -m live`, or for a single one, `source .venv/bin/activate && RUN_LIVE_OPENAI=1 pytest tests/test_openai_live.py -k "accepts_tools_live and gpt-4o-2024-05-13" -m live`
4. Update provider docs with parameter support based on tests (system prompt, temperature/top_p, reasoning, tools, max output constraints). Treat tests as the arbiter of uncertain assumptions (e.g. of parameter support); surface when different than expected. If the new model has a different kind of default parameters, then the runners (for puzzles and for baselines) will also need to be updated.
5. Update model_release_registry (docs/model_release_registry.md) with our system's support for that model. Mark that model in bold in README "Model landscape" year-by-year table.
6. (Will leads from here) After a model is ready, it can be run against existing puzzles and the baselines, using the catch_up.py script
7. Create new plots with generate_comparison.py. (need to --recompute-points for both, add model alias if needed within visualize.py) 
8. Confirm README text 
  - new plot will be automatically linked, but might require edits in the caption and above about 'where' certain models are, since these aren't stable
  - 'X LLMs are currently supported' in intro will need to be edited/incremented
  - 'Recently added' should be changed
9. Regenerate compendium of all responses using generate_compendium.py

Remember, after merging, the live site will take an hour or two to catch up since the readme links to the same file path for the figure.

- All open-weights models are run through Fireworks and require mapping; see below.
- Use snapshot model names (e.g., `o3-2025-04-16`). If snapshot names not available (e.g. `gemini-2.5-flash`), make a note of that.

### Fireworks-specific (open-weights models)
- Add alias→canonical mapping in `CANONICAL_MODELS` (e.g., `"deepseek-v3p2": "accounts/fireworks/models/deepseek-v3p2"`).
- Add to `MODEL_DEFAULTS`, `PRICE_SCHEDULES_USD_PER_MILLION`, `MODEL_ALIASES`, `MODEL_PROVIDERS`.
- If reasoning model, add to `REASONING_MODELS` set (enables auto `reasoning_effort="hight"`).

## Marking a model unreachable

When a model becomes unavailable (deprecated by provider, removed from Fireworks serverless, etc.):

- Add the model to `UNREACHABLE_MODELS` in `src/batch_runner.py` as a `(storage_provider, storage_model_name)` tuple.
- Include a comment with the date you discovered it was unreachable and any relevant context (e.g., provider deprecation notice, Fireworks removal).
- The model remains in provider metadata (pricing, aliases, etc.) since we have historical responses.
- `--model ALL` will exclude unreachable models; `list_models` shows them in a separate "Unreachable" section, and will exclude them from the count.
- Open-source models may become reachable again if re-hosted; check availability before each puzzle run and remove from `UNREACHABLE_MODELS` if restored.

## Adding a puzzle

Each new puzzle follows a structured development cycle:

### 1. Branch and iterate
- Create a feature branch named with the expected puzzle name (e.g., `conceptual-metaphor`).
- Start at v0.1 and increment toward v0.5 as you iterate on the puzzle text.

### 2. Version conventions
- **v0.1–0.4**: Working drafts during iteration.
- **v0.5** is the quasi-canonical version (current max). This version:
  - Will be used to generate scoring rubrics (and is therefore "contaminated" from a rigorous perspective—hence not yet 1.0).
  - May be circulated for review in case unexpected prompt issues emerge and need fixing.
- **v1.0** means "locked for publication" (as noted in Principles).

### 3. Generate responses
- Run the puzzle against all reachable models.
- Capture responses following standard storage conventions.

### 4. Regenerate plots
- Per-puzzle plot (single puzzle visualization).
- Aggregated philosophy plot (all philosophy puzzles combined).
- Comparison plot (baseline vs philosophy side-by-side).
  - Use `philosophy_all` to aggregate all puzzles; pairwise distances are computed per puzzle and then averaged.
  - Comparison is only at the total (all-puzzles) level, not per puzzle.
  - Quick run: `python -m scripts.generate_comparison <puzzle> --emit-all`.

### 5. Update README
- Add the new puzzle to the README timeline/listing.
- Include generated plots as appropriate.

### 6. Merge branch
- Open a PR to merge the feature branch.
- PR body should summarize new findings from the puzzle responses.
- Embed the new puzzle's plot in the PR description.
- Include before/after versions of the all-philosophy aggregated plot to show impact.

## Tests
- Use `pytest` for lightweight tests around loaders and request assembly.
- Keep tests small and local; avoid network calls unless explicitly marked live.
- Live tests must be opt-in, cost-labeled, and gated by environment variables.
- Prefer tests that validate expected use/nonuse of: system prompt, temperature, max output
  length, reasoning effort, tool usage (where supported).
- When asserting a parameter is unsupported on a reasoning-capable model, explicitly enable
  reasoning in the request so the test matches default runner behavior.
- Group tests by their purpose
- Parametrize each test, manually add the relevant model name in as part of an array (will be useful as we add more models)


## Provider handling
- Normalize across providers with a thin adapter interface, at src/providers/{provider}.py
- Keep per-provider quirks isolated to their adapter.
- Provide a dry-run mode that writes request payloads without sending them.
- Default to the highest available reasoning effort per model.
- Request the most detailed reasoning visibility available for the model.
- Omit tool configuration entirely unless tools are required.
- Target providers: OpenAI, Anthropic, Gemini, plus open-source models via Fireworks.
- Provider API syntax lives in provider-specific docs under `docs/providers/`.

### Adding a new provider (best practices + coverage)
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


## Baselines
Baseline prompts establish a "normal" level of model differentiation to contrast with philosophy puzzle responses. The goal is to measure: "How much do models differ on unimportant opinion questions?" and then compare whether philosophy-of-self questions elicit at least as much (ideally more) differentiation.

### Baseline prompt design
- All prompts follow the form: "What do you think is the most interesting X? {follow-up}"
- Topics are chosen to elicit minimal preferences without philosophical weight.
- Follow-ups vary to produce genre-diverse outputs (programming, math, fiction, biology, etc.), comparable in length range to philosophy responses, and which vary in their style based on the top-level answer (e.g. 500 words of Shakespeare would be very different than 500 more words of Frankenstein) - this makes them helpful contrasts for MDS, compared to the philosophy puzzles. Some use simple "How so?" follow-ups; others request extended output in a specific register (e.g., "Compose a short 500-word addition", "Write a day-in-the-life sketch").

### Running baselines
```bash
# Clear cached responses and embeddings before re-running with new prompts
rm -rf baselines/responses/
rm analysis/embeddings/*__baseline__*

# Default behavior is resume (skip prompts already captured). Use --no-resume to force reruns.
# Use baseline runs as part of the "add new model" checklist.

# Run baselines for specific models
python -m scripts.run_baselines --model gpt-4-0613 gemini-2.0-flash-lite-001 o3-2025-04-16 claude-opus-4-5-20251101
```

### Generating visualizations
```bash
# Side-by-side comparison of baseline vs philosophy responses
# Points are rescaled so baseline and philosophy maps share the same axis scale
python -m scripts.generate_comparison panopticon
python -m scripts.generate_comparison panopticon sapir_whorf  # multiple puzzles averaged

# Philosophy-only mode: show just the philosophy puzzle map(s) without baseline
# No rescaling is applied since there's no baseline to match
python -m scripts.generate_comparison panopticon --philosophy-only
python -m scripts.generate_comparison panopticon sapir_whorf --philosophy-only
```

### Embedding cache
- Embeddings are cached in `analysis/embeddings/` as `.npz` files.
- Filename format: `{provider}__{model}__{type}__{name}__all-mpnet-base-v2.npz`
- `type` is either `baseline` or `puzzle`.
- Baseline embeddings must be cleared when prompts change; puzzle embeddings can persist.
