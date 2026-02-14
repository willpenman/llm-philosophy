"""Run a single puzzle with a provider adapter, or all models with --model ALL."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.providers.anthropic import supports_model as anthropic_supports_model
from src.providers.gemini import supports_model as gemini_supports_model
from src.providers.grok import supports_model as grok_supports_model
from src.providers.openai import supports_model as openai_supports_model
from src.providers.fireworks import supports_model as fireworks_supports_model
from src.runner import (
    run_anthropic_puzzle,
    run_gemini_puzzle,
    run_grok_puzzle,
    run_openai_puzzle,
    run_fireworks_puzzle,
)
from src.batch_runner import (
    enumerate_all_models,
    filter_models,
    run_batch,
    ExecutionMode,
)
from src.puzzles import load_puzzle

ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _optional_path(value: str | None) -> Path | None:
    if value is None:
        return None
    return Path(value)


def _run_batch_mode(args: argparse.Namespace) -> None:
    """Handle batch execution when --model ALL or multiple models are specified."""
    # Load puzzle to get version
    puzzle = load_puzzle(args.name)

    # Get all available models
    all_specs = enumerate_all_models()

    # Determine provider filter
    provider_filter = args.providers
    if provider_filter is None and args.provider is not None:
        provider_filter = [args.provider]

    # Filter models based on args
    specs = filter_models(all_specs, args.model, provider_filter)

    if not specs:
        print("No models match the specified filters.")
        return

    # Parse execution mode
    mode = ExecutionMode(args.mode)

    # Run batch
    run_batch(
        puzzle_name=args.name,
        puzzle_version=puzzle.version,
        specs=specs,
        mode=mode,
        responses_dir=ROOT / "responses",
        resume=args.resume,
        dry_run=args.dry_run,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one puzzle against a single provider model, or all models with --model ALL."
    )
    parser.add_argument("name", help="Puzzle name (filename without .py)")
    parser.add_argument(
        "--model",
        nargs="+",
        required=True,
        help="Model name(s), or ALL to run all models",
    )
    parser.add_argument(
        "--provider",
        default=None,
        choices=["openai", "gemini", "anthropic", "grok", "fireworks"],
        help="Override provider selection (single model) or filter providers (batch mode)",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["openai", "gemini", "anthropic", "grok", "fireworks"],
        default=None,
        help="Filter to specific providers (batch mode only)",
    )
    parser.add_argument(
        "--mode",
        choices=["sequential", "parallel-provider", "parallel-all"],
        default="sequential",
        help="Execution mode for batch runs (default: sequential)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip models that already have responses for this puzzle+version",
    )
    parser.add_argument("--max-output-tokens", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--special-settings", default=None)
    parser.add_argument(
        "--streaming",
        choices=["true", "false"],
        default=None,
        help="Override streaming behavior (true/false).",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--debug-sse",
        action="store_true",
        help="Capture raw SSE/stream events to a debug file and skip request/response storage.",
    )
    args = parser.parse_args()

    _load_dotenv(ROOT / ".env")

    # Check if this is a batch run (--model ALL or multiple models)
    is_batch = "ALL" in args.model or len(args.model) > 1
    if is_batch:
        _run_batch_mode(args)
        return

    stream_override = None
    if args.streaming is not None:
        stream_override = args.streaming == "true"

    # Single model mode - use the first (and only) model
    model = args.model[0]

    if args.provider == "gemini":
        result = run_gemini_puzzle(
            puzzle_name=args.name,
            model=model,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            special_settings=args.special_settings,
            dry_run=args.dry_run,
            debug_sse=args.debug_sse,
            stream=stream_override if stream_override is not None else True,
        )
    elif args.provider == "openai":
        result = run_openai_puzzle(
            puzzle_name=args.name,
            model=model,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            special_settings=args.special_settings,
            dry_run=args.dry_run,
            debug_sse=args.debug_sse,
            stream=stream_override if stream_override is not None else True,
        )
    elif args.provider == "anthropic":
        result = run_anthropic_puzzle(
            puzzle_name=args.name,
            model=model,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            special_settings=args.special_settings,
            dry_run=args.dry_run,
            debug_sse=args.debug_sse,
            stream=stream_override if stream_override is not None else True,
        )
    elif args.provider == "grok":
        result = run_grok_puzzle(
            puzzle_name=args.name,
            model=model,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            special_settings=args.special_settings,
            dry_run=args.dry_run,
            debug_sse=args.debug_sse,
            stream=stream_override if stream_override is not None else False,
        )
    elif args.provider == "fireworks":
        result = run_fireworks_puzzle(
            puzzle_name=args.name,
            model=model,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            special_settings=args.special_settings,
            dry_run=args.dry_run,
            debug_sse=args.debug_sse,
            stream=stream_override if stream_override is not None else True,
        )
    else:
        openai_supported = openai_supports_model(model)
        gemini_supported = gemini_supports_model(model)
        anthropic_supported = anthropic_supports_model(model)
        grok_supported = grok_supports_model(model)
        fireworks_supported = fireworks_supports_model(model)
        matches = [name for name, ok in {
            "openai": openai_supported,
            "gemini": gemini_supported,
            "anthropic": anthropic_supported,
            "grok": grok_supported,
            "fireworks": fireworks_supported,
        }.items() if ok]
        if len(matches) > 1:
            raise ValueError(
                f"Model {model} matches multiple providers; pass --provider to select."
            )
        if gemini_supported:
            result = run_gemini_puzzle(
                puzzle_name=args.name,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                top_k=args.top_k,
                special_settings=args.special_settings,
                dry_run=args.dry_run,
                debug_sse=args.debug_sse,
                stream=stream_override if stream_override is not None else True,
            )
        elif anthropic_supported:
            result = run_anthropic_puzzle(
                puzzle_name=args.name,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                top_k=args.top_k,
                special_settings=args.special_settings,
                dry_run=args.dry_run,
                debug_sse=args.debug_sse,
                stream=stream_override if stream_override is not None else True,
            )
        elif openai_supported:
            result = run_openai_puzzle(
                puzzle_name=args.name,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
                special_settings=args.special_settings,
                dry_run=args.dry_run,
                debug_sse=args.debug_sse,
                stream=stream_override if stream_override is not None else True,
            )
        elif grok_supported:
            result = run_grok_puzzle(
                puzzle_name=args.name,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                special_settings=args.special_settings,
                dry_run=args.dry_run,
                debug_sse=args.debug_sse,
                stream=stream_override if stream_override is not None else False,
            )
        elif fireworks_supported:
            result = run_fireworks_puzzle(
                puzzle_name=args.name,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                special_settings=args.special_settings,
                dry_run=args.dry_run,
                debug_sse=args.debug_sse,
                stream=stream_override if stream_override is not None else True,
            )
        else:
            raise ValueError(
                f"Unknown model {model}; pass --provider to override."
            )

    if result.sse_event_path is not None:
        print(f"sse_event_path={result.sse_event_path}")


if __name__ == "__main__":
    main()
