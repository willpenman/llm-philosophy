"""Run a single puzzle with a provider adapter."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from providers.anthropic import supports_model as anthropic_supports_model  # noqa: E402
from providers.gemini import supports_model as gemini_supports_model  # noqa: E402
from providers.openai import supports_model as openai_supports_model  # noqa: E402
from src.runner import (  # noqa: E402
    run_anthropic_puzzle,
    run_gemini_puzzle,
    run_openai_puzzle,
)


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one puzzle against a single provider model."
    )
    parser.add_argument("name", help="Puzzle name (filename without .py)")
    parser.add_argument(
        "--model",
        required=True,
        help="Model name (used to select provider automatically)",
    )
    parser.add_argument(
        "--provider",
        default=None,
        choices=["openai", "gemini", "anthropic"],
        help="Override provider selection",
    )
    parser.add_argument("--max-output-tokens", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--special-settings", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--debug-openai-sse",
        action="store_true",
        help="Capture raw OpenAI SSE events to a debug file and skip request/response storage.",
    )
    args = parser.parse_args()

    _load_dotenv(ROOT / ".env")

    if args.provider == "gemini":
        if args.debug_openai_sse:
            raise ValueError("--debug-openai-sse only applies to OpenAI runs.")
        model = args.model
        result = run_gemini_puzzle(
            puzzle_name=args.name,
            model=model,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            special_settings=args.special_settings,
            dry_run=args.dry_run,
        )
    elif args.provider == "openai":
        model = args.model
        result = run_openai_puzzle(
            puzzle_name=args.name,
            model=model,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            special_settings=args.special_settings,
            dry_run=args.dry_run,
            debug_sse=args.debug_openai_sse,
        )
    elif args.provider == "anthropic":
        if args.debug_openai_sse:
            raise ValueError("--debug-openai-sse only applies to OpenAI runs.")
        model = args.model
        result = run_anthropic_puzzle(
            puzzle_name=args.name,
            model=model,
            max_output_tokens=args.max_output_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            special_settings=args.special_settings,
            dry_run=args.dry_run,
        )
    else:
        model = args.model
        openai_supported = openai_supports_model(model)
        gemini_supported = gemini_supports_model(model)
        anthropic_supported = anthropic_supports_model(model)
        matches = [name for name, ok in {
            "openai": openai_supported,
            "gemini": gemini_supported,
            "anthropic": anthropic_supported,
        }.items() if ok]
        if len(matches) > 1:
            raise ValueError(
                f"Model {model} matches multiple providers; pass --provider to select."
            )
        if gemini_supported:
            if args.debug_openai_sse:
                raise ValueError("--debug-openai-sse only applies to OpenAI runs.")
            result = run_gemini_puzzle(
                puzzle_name=args.name,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                top_k=args.top_k,
                special_settings=args.special_settings,
                dry_run=args.dry_run,
            )
        elif anthropic_supported:
            if args.debug_openai_sse:
                raise ValueError("--debug-openai-sse only applies to OpenAI runs.")
            result = run_anthropic_puzzle(
                puzzle_name=args.name,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                top_k=args.top_k,
                special_settings=args.special_settings,
                dry_run=args.dry_run,
            )
        elif openai_supported:
            result = run_openai_puzzle(
                puzzle_name=args.name,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
                special_settings=args.special_settings,
                dry_run=args.dry_run,
                debug_sse=args.debug_openai_sse,
            )
        else:
            raise ValueError(
                f"Unknown model {model}; pass --provider to override."
            )

    if result.sse_event_path is not None:
        print(f"sse_event_path={result.sse_event_path}")


if __name__ == "__main__":
    main()
