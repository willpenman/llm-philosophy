# AGENTS.md

## Mission
Build a small Python framework for running philosophy-style LLM evaluations with a shared system prompt, a library of puzzles, and reproducible capture of requests and responses across providers.

## Development
- Use python (3.13) through the venv: `source .venv/bin/activate`
- Task wrap-up: 
  - Document any long-term insights about agent abilities and directions here, e.g. access
  - Document progress and todos in spec.md
  - Reserve README for public-facing notes, e.g. model support, features, etc.

## Puzzle focus
- Puzzles are meant to be specific to LLM ontology and contemporary model behavior, not restating classic philosophical puzzles.

## Testing guidance
- Prefer minimal, local tests that validate core invariants and avoid external dependencies.
- Keep tests offline and deterministic; avoid provider calls until adapters exist.

## Working agreement
- Keep specs lightweight and editable; store detailed conventions in `docs/spec.md`.
- Prefer append-only data storage with clear provenance and timestamps.
- Favor minimal abstractions and small modules over heavy frameworks.
- Preserve provider payloads verbatim; normalize only when it adds clear value.
- Treat prompts as fixtures; avoid runtime mutation.

## How to collaborate here
- When in doubt, ask for a quick clarification rather than over-designing.
- Propose the smallest next change that unblocks progress.
- Call out tradeoffs and leave TODOs rather than guessing.

## Pointers
- Detailed storage conventions, JSONL schema sketch, and provider notes live in `docs/spec.md`.
