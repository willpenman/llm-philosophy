# AGENTS.md

## Mission
Design and implement a small Python framework for running philosophy-style LLM evaluations. The framework should support a single, reusable system prompt (one paragraph) and a library of multi-paragraph philosophy puzzles. It must run the same prompt set across multiple providers, save all sent prompts, received responses, and metadata (prefer JSONL), and also produce a human-friendly output format for review.

## Operating principles
- Keep the system prompt short, stable, and provider-agnostic.
- Treat puzzles as versioned, standalone fixtures.
- Capture every run deterministically with full metadata.
- Prioritize reproducibility and traceability over performance.

## Expected repo shape (propose and refine)
- `prompts/`
  - `system.py` (one paragraph prompt with annotations)
  - `puzzles/` (each puzzle as a few paragraphs, stored as `.py`)
- `runs/` (JSONL + human-readable outputs)
- `providers/` (provider adapters and config handling)
- `scripts/` (CLI entry points)
- `src/` (core framework code)

## Data capture requirements
- Log the exact system prompt and puzzle text per request.
- Store all metadata - provider name, model name, temperature, max tokens (always set to model max), stop sequences, seed, thinking tokens, request IDs...
- Record model cost structure (input/output pricing) to compute per-run cost.
- Persist timing info (request start/end, latency).
- Keep request/response pairs in JSONL for aggregation.
- Generate a readable format that is just the raw response text (one file per response).
- Leave room for analysis workflows (possibly in a separate repo linked by run IDs).

## Provider handling
- Normalize across providers with a thin adapter interface.
- Keep per-provider quirks isolated to their adapter.
- Avoid hardcoding credentials; use environment variables.
- Provide a dry-run mode that writes the request payloads without sending them.
- Target providers: OpenAI, Anthropic, Gemini, plus open-source models via Fireworks.
- TODO: include links to each provider's dev docs.
- Future: enable synchronous calls to support fast "run all models for this puzzle" and "run all puzzles for this model."

## Work style
- Favor clear, minimal code and small modules.
- Add succinct comments.
- Prefer deterministic filenames and timestamps for runs.

## Next steps to start
1. Propose a minimal directory structure and file format conventions.
2. Draft the one-paragraph system prompt and 2–3 example puzzles.
3. Sketch the provider adapter interface and a JSONL schema.
4. Implement a small CLI to run a batch and write outputs.
