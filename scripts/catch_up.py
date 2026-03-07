"""Run baselines and all puzzles for one or more models.

This script brings new models up to parity with existing ones by running:
1. All baseline prompts (for embedding comparison)
2. All puzzles (philosophy responses)

Usage:
    # Dry run to see what would happen
    python -m scripts.catch_up --model gpt-5.4-2026-03-05 --dry-run

    # Run catch-up for specific models
    python -m scripts.catch_up --model gpt-5.4-2026-03-05 gpt-5.4-pro-2026-03-05

    # Skip baselines (only run puzzles)
    python -m scripts.catch_up --model gpt-5.4-2026-03-05 --skip-baselines

    # Skip puzzles (only run baselines)
    python -m scripts.catch_up --model gpt-5.4-2026-03-05 --skip-puzzles
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from baselines.prompts import BASELINE_PROMPTS
from scripts.run_baselines import (
    has_baseline_response,
    run_all_baselines_for_model,
    _get_provider_for_model,
)
from src.batch_runner import (
    enumerate_all_models,
    filter_models,
    find_existing_responses,
    ModelSpec,
)
from src.puzzles import list_puzzle_names, load_puzzle
from src.runner import (
    run_openai_puzzle,
    run_anthropic_puzzle,
    run_gemini_puzzle,
    run_grok_puzzle,
    run_fireworks_puzzle,
)

ROOT = Path(__file__).resolve().parents[1]
RESPONSES_DIR = ROOT / "responses"
BASELINES_DIR = ROOT / "baselines" / "responses"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _run_puzzle_for_model(
    puzzle_name: str,
    model: str,
    runner_provider: str,
    dry_run: bool = False,
) -> bool:
    """Run a single puzzle for a model. Returns True on success."""
    if dry_run:
        print(f"    [dry-run] {puzzle_name}")
        return True

    try:
        print(f"    [run] {puzzle_name}...", end=" ", flush=True)

        if runner_provider == "openai":
            result = run_openai_puzzle(puzzle_name=puzzle_name, model=model, stream=True)
        elif runner_provider == "anthropic":
            result = run_anthropic_puzzle(puzzle_name=puzzle_name, model=model, stream=True)
        elif runner_provider == "gemini":
            result = run_gemini_puzzle(puzzle_name=puzzle_name, model=model, stream=True)
        elif runner_provider == "grok":
            result = run_grok_puzzle(puzzle_name=puzzle_name, model=model, stream=False)
        elif runner_provider == "fireworks":
            result = run_fireworks_puzzle(puzzle_name=puzzle_name, model=model, stream=True)
        else:
            print(f"ERROR: Unknown provider {runner_provider}")
            return False

        print("done")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def get_missing_baselines(provider: str, model: str) -> list[str]:
    """Return list of baseline prompt names that are missing for this model."""
    missing = []
    for prompt in BASELINE_PROMPTS:
        if not has_baseline_response(provider, model, prompt.name):
            missing.append(prompt.name)
    return missing


def get_missing_puzzles(
    provider: str,
    model: str,
    puzzle_names: list[str],
) -> list[tuple[str, str]]:
    """Return list of (puzzle_name, version) that are missing for this model."""
    missing = []
    for puzzle_name in puzzle_names:
        puzzle = load_puzzle(puzzle_name)
        existing = find_existing_responses(puzzle_name, puzzle.version, RESPONSES_DIR)
        if (provider, model) not in existing:
            missing.append((puzzle_name, puzzle.version or "unknown"))
    return missing


def run_catch_up_for_model(
    spec: ModelSpec,
    puzzle_names: list[str],
    *,
    skip_baselines: bool = False,
    skip_puzzles: bool = False,
    dry_run: bool = False,
) -> tuple[int, int, int, int]:
    """Run catch-up for a single model.

    Returns (baselines_run, baselines_skipped, puzzles_run, puzzles_skipped).
    """
    baselines_run = 0
    baselines_skipped = 0
    puzzles_run = 0
    puzzles_skipped = 0

    print(f"\n{'=' * 60}")
    print(f"Model: {spec.display_name}")
    print(f"  Storage: {spec.provider}/{spec.model}")
    print(f"  Runner: {spec.runner_provider}")
    print("=" * 60)

    # Phase 1: Baselines
    if not skip_baselines:
        missing_baselines = get_missing_baselines(spec.provider, spec.model)
        total_baselines = len(BASELINE_PROMPTS)
        baselines_skipped = total_baselines - len(missing_baselines)

        print(f"\n  Baselines: {len(missing_baselines)} to run, {baselines_skipped} already done")

        if missing_baselines:
            # Use the existing baseline runner
            run_all_baselines_for_model(
                model=spec.model,
                storage_provider=spec.provider,
                runner_provider=spec.runner_provider,
                resume=True,
                dry_run=dry_run,
            )
            baselines_run = len(missing_baselines)
    else:
        print("\n  Baselines: skipped (--skip-baselines)")

    # Phase 2: Puzzles
    if not skip_puzzles:
        missing_puzzles = get_missing_puzzles(spec.provider, spec.model, puzzle_names)
        total_puzzles = len(puzzle_names)
        puzzles_skipped = total_puzzles - len(missing_puzzles)

        print(f"\n  Puzzles: {len(missing_puzzles)} to run, {puzzles_skipped} already done")

        for puzzle_name, version in missing_puzzles:
            if dry_run:
                print(f"    [dry-run] {puzzle_name} (v{version})")
                puzzles_run += 1
            else:
                success = _run_puzzle_for_model(
                    puzzle_name=puzzle_name,
                    model=spec.model,
                    runner_provider=spec.runner_provider,
                    dry_run=dry_run,
                )
                if success:
                    puzzles_run += 1
    else:
        print("\n  Puzzles: skipped (--skip-puzzles)")

    return baselines_run, baselines_skipped, puzzles_run, puzzles_skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run baselines and puzzles for new models to bring them up to parity."
    )
    parser.add_argument(
        "--model",
        nargs="+",
        required=True,
        help="Model name(s) to catch up",
    )
    parser.add_argument(
        "--skip-baselines",
        action="store_true",
        help="Skip running baselines",
    )
    parser.add_argument(
        "--skip-puzzles",
        action="store_true",
        help="Skip running puzzles",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without executing",
    )
    args = parser.parse_args()

    _load_dotenv(ROOT / ".env")

    # Get all available model specs
    all_specs = enumerate_all_models()

    # Filter to requested models
    specs = filter_models(all_specs, args.model, None)

    if not specs:
        print(f"No matching models found for: {args.model}")
        print("\nAvailable models:")
        for spec in all_specs[:10]:
            print(f"  - {spec.model} ({spec.display_name})")
        if len(all_specs) > 10:
            print(f"  ... and {len(all_specs) - 10} more")
        return

    # Get all puzzle names
    puzzle_names = list_puzzle_names()

    print(f"Catch-up for {len(specs)} model(s)")
    print(f"Baselines: {len(BASELINE_PROMPTS)} prompts")
    print(f"Puzzles: {len(puzzle_names)} puzzles ({', '.join(puzzle_names)})")

    if args.dry_run:
        print("\n*** DRY RUN MODE ***")

    # Totals
    total_baselines_run = 0
    total_baselines_skipped = 0
    total_puzzles_run = 0
    total_puzzles_skipped = 0

    for spec in specs:
        b_run, b_skip, p_run, p_skip = run_catch_up_for_model(
            spec=spec,
            puzzle_names=puzzle_names,
            skip_baselines=args.skip_baselines,
            skip_puzzles=args.skip_puzzles,
            dry_run=args.dry_run,
        )
        total_baselines_run += b_run
        total_baselines_skipped += b_skip
        total_puzzles_run += p_run
        total_puzzles_skipped += p_skip

    # Summary
    print("\n" + "=" * 60)
    print("CATCH-UP SUMMARY")
    print("=" * 60)
    print(f"Models processed: {len(specs)}")
    if not args.skip_baselines:
        print(f"Baselines run:    {total_baselines_run}")
        print(f"Baselines skipped:{total_baselines_skipped}")
    if not args.skip_puzzles:
        print(f"Puzzles run:      {total_puzzles_run}")
        print(f"Puzzles skipped:  {total_puzzles_skipped}")
    print("\nDone!")


if __name__ == "__main__":
    main()
