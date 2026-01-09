# AGENTS.md

## Mission
Build a small Python framework for running philosophy-style LLM evaluations with a shared system prompt, a library of puzzles, and reproducible capture of requests and responses across providers.

## Development
- Use python (3.13) through the venv: `source .venv/bin/activate`
- For API reference, do not trust your intuition. Consult local docs in provider-specific file (e.g. `providers/openai.md`) and/or use web search to identify current api syntax. When unsure, highlight to user and wait to finish the task until given confirmation.
- Task wrap-up: 
  - Document any long-term insights about agent abilities and directions here
  - Document progress and todos in spec.md. Remove pre-existing todos that have already been done or are deprecated
  - Document model-specific parameter availability in the provider-speicfic file.
  - Reserve README for public-facing notes, e.g. model support, features, etc.

## Puzzle focus
- Puzzles are meant to be specific to LLM ontology and contemporary model behavior, not restating classic philosophical puzzles.

## Testing guidance
- Prefer minimal, local tests that validate core invariants and avoid external dependencies.
- When adding new provider/model functionality, create tests that verify the parameters and values most relevant to this eval suite: system prompt, temperature, max output length, level of reasoning/thinking, tool use. These differ per model and some models may not have these available!
- Consider existing tests before adding new ones; do not duplicate tests.
- When adding support for a new model, use the parametrize lists to add it per live test; test only the new one by passing the -k flag
- Paid/live provider tests must be opt-in and clearly labeled with cost and env requirements (e.g., `@pytest.mark.live`, `RUN_LIVE_OPENAI=1`, `OPENAI_API_KEY`). Default runs should skip them.

## Working agreement
- Keep specs lightweight and editable; store detailed conventions in `docs/spec.md`.
- Prefer append-only data storage with clear provenance and timestamps.
- Favor minimal abstractions and small modules over heavy frameworks.
- Preserve provider payloads verbatim; normalize only when it adds clear value.
- Treat prompts as fixtures; avoid runtime mutation.

## How to collaborate here
- When in doubt, ask for a quick clarification rather than over-designing. If 'progress' from the spec seems to not be either, request clarification rather than adding it back in yourself; it may have been an intentional choice and therefore need revision.
- Call out tradeoffs and leave TODOs rather than guessing.

## Pointers
- Detailed storage conventions, JSONL schema sketch, and provider notes live in `docs/spec.md`.

## Long-term insights
- Cost modeling needs to support multi-tier pricing (modality, service tier, long-output tiers like Gemini) beyond simple input/output rates.
