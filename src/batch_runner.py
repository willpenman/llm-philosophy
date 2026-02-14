"""Batch runner for executing puzzles against multiple models."""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import threading
import time
from typing import Any, Callable

from src.providers.openai import (
    SUPPORTED_MODELS as OPENAI_MODELS,
    display_model_name as openai_display_model_name,
)
from src.providers.anthropic import (
    SUPPORTED_MODELS as ANTHROPIC_MODELS,
    display_model_name as anthropic_display_model_name,
)
from src.providers.gemini import (
    SUPPORTED_MODELS as GEMINI_MODELS,
    display_model_name as gemini_display_model_name,
)
from src.providers.grok import (
    SUPPORTED_MODELS as GROK_MODELS,
    display_model_name as grok_display_model_name,
)
from src.providers.fireworks import (
    CANONICAL_MODELS as FIREWORKS_CANONICAL_MODELS,
    display_model_name as fireworks_display_model_name,
    provider_for_model as fireworks_provider_for_model,
    storage_model_name as fireworks_storage_model_name,
)
from src.runner import (
    run_openai_puzzle,
    run_anthropic_puzzle,
    run_gemini_puzzle,
    run_grok_puzzle,
    run_fireworks_puzzle,
    RunResult,
)


class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL_PROVIDER = "parallel-provider"
    PARALLEL_ALL = "parallel-all"


class RunStatus(Enum):
    PENDING = "pending"
    STARTED = "started"
    RECEIVING = "receiving"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class ModelSpec:
    """Identifies a unique model to run."""

    provider: str  # Storage provider (openai, anthropic, deepseek, etc.)
    model: str  # Model ID for storage
    display_name: str  # Human-readable name
    runner_provider: str  # Which run_*_puzzle to use (openai, anthropic, gemini, grok, fireworks)


@dataclass
class ModelRunResult:
    """Result of running a single model."""

    spec: ModelSpec
    status: RunStatus
    run_result: RunResult | None = None
    error: str | None = None
    duration_seconds: float = 0.0


# Map runner_provider to the appropriate run function
RUNNER_MAP: dict[str, Callable[..., RunResult]] = {
    "openai": run_openai_puzzle,
    "anthropic": run_anthropic_puzzle,
    "gemini": run_gemini_puzzle,
    "grok": run_grok_puzzle,
    "fireworks": run_fireworks_puzzle,
}

# Default streaming settings per provider
STREAM_DEFAULTS: dict[str, bool] = {
    "openai": True,
    "anthropic": True,
    "gemini": True,
    "grok": False,  # Streaming loses usage stats
    "fireworks": True,
}


def enumerate_all_models() -> list[ModelSpec]:
    """Build a flat list of all (provider, model) pairs across all providers."""
    specs: list[ModelSpec] = []

    # OpenAI
    for model in sorted(OPENAI_MODELS):
        specs.append(
            ModelSpec(
                provider="openai",
                model=model,
                display_name=openai_display_model_name(model),
                runner_provider="openai",
            )
        )

    # Anthropic
    for model in sorted(ANTHROPIC_MODELS):
        specs.append(
            ModelSpec(
                provider="anthropic",
                model=model,
                display_name=anthropic_display_model_name(model),
                runner_provider="anthropic",
            )
        )

    # Gemini
    for model in sorted(GEMINI_MODELS):
        specs.append(
            ModelSpec(
                provider="gemini",
                model=model,
                display_name=gemini_display_model_name(model),
                runner_provider="gemini",
            )
        )

    # Grok
    for model in sorted(GROK_MODELS):
        specs.append(
            ModelSpec(
                provider="grok",
                model=model,
                display_name=grok_display_model_name(model),
                runner_provider="grok",
            )
        )

    # Fireworks (DeepSeek, Qwen, Kimi, Meta)
    for alias in sorted(FIREWORKS_CANONICAL_MODELS.keys()):
        storage_name = fireworks_storage_model_name(alias)
        storage_provider = fireworks_provider_for_model(alias)
        specs.append(
            ModelSpec(
                provider=storage_provider,
                model=storage_name,
                display_name=fireworks_display_model_name(alias),
                runner_provider="fireworks",
            )
        )

    return specs


def filter_models(
    all_specs: list[ModelSpec],
    model_args: list[str] | None,
    provider_args: list[str] | None,
) -> list[ModelSpec]:
    """Filter model specs based on CLI arguments.

    Args:
        all_specs: Full list of available model specs
        model_args: List of model names, or ["ALL"] for all models
        provider_args: Optional list of providers to filter by
    """
    specs = all_specs

    # Filter by provider first if specified
    if provider_args:
        runner_providers = set(provider_args)
        specs = [s for s in specs if s.runner_provider in runner_providers]

    # If model_args is None or ["ALL"], return all (filtered by provider)
    if model_args is None or model_args == ["ALL"]:
        return specs

    # Otherwise filter to specific models
    model_set = set(model_args)
    return [s for s in specs if s.model in model_set or s.display_name in model_set]


def find_existing_responses(
    puzzle_name: str,
    puzzle_version: str | None,
    responses_dir: Path,
) -> set[tuple[str, str]]:
    """Find all (provider, model) pairs that already have responses for this puzzle+version.

    Args:
        puzzle_name: The puzzle name to check
        puzzle_version: The puzzle version to match (None matches any version)
        responses_dir: Base directory for responses (typically "responses/")

    Returns:
        Set of (provider, model) tuples that have existing responses
    """
    existing: set[tuple[str, str]] = set()

    if not responses_dir.exists():
        return existing

    # Iterate through all responses.jsonl files
    for jsonl_path in responses_dir.rglob("responses.jsonl"):
        # Extract provider and model from path: responses/{provider}/{model}/responses.jsonl
        try:
            rel_parts = jsonl_path.relative_to(responses_dir).parts
        except ValueError:
            continue
        if len(rel_parts) < 3:
            continue
        provider, model = rel_parts[0], rel_parts[1]

        # Scan the JSONL file for matching puzzle+version
        try:
            with jsonl_path.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("puzzle_name") != puzzle_name:
                            continue
                        if puzzle_version is not None:
                            if record.get("puzzle_version") != puzzle_version:
                                continue
                        # Found a match!
                        existing.add((provider, model))
                        break  # Only need one match per file
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue

    return existing


def run_single_model(
    spec: ModelSpec,
    puzzle_name: str,
    *,
    status_callback: Callable[[ModelSpec, RunStatus], None] | None = None,
    quiet: bool = False,
) -> ModelRunResult:
    """Execute a single model run and return the result.

    Args:
        spec: The model specification
        puzzle_name: Name of the puzzle to run
        status_callback: Optional callback for status updates
        quiet: If True, suppress streaming output (for parallel modes)
    """
    runner_fn = RUNNER_MAP.get(spec.runner_provider)
    if runner_fn is None:
        return ModelRunResult(
            spec=spec,
            status=RunStatus.FAILED,
            error=f"Unknown runner provider: {spec.runner_provider}",
        )

    # Report started
    if status_callback:
        status_callback(spec, RunStatus.STARTED)

    stream = STREAM_DEFAULTS.get(spec.runner_provider, True)
    start_time = time.perf_counter()

    try:
        # For fireworks, we pass the storage model name (alias)
        model_arg = spec.model

        # Always use streaming - it's needed to avoid read timeouts on long responses.
        # The 'quiet' flag only suppresses console output, not the streaming itself.
        result = runner_fn(
            puzzle_name=puzzle_name,
            model=model_arg,
            stream=stream,
        )

        duration = time.perf_counter() - start_time

        # Report receiving (we got a response)
        if status_callback:
            status_callback(spec, RunStatus.RECEIVING)

        return ModelRunResult(
            spec=spec,
            status=RunStatus.COMPLETED,
            run_result=result,
            duration_seconds=duration,
        )
    except Exception as e:
        duration = time.perf_counter() - start_time
        return ModelRunResult(
            spec=spec,
            status=RunStatus.FAILED,
            error=str(e),
            duration_seconds=duration,
        )


def _print_status(spec: ModelSpec, status: RunStatus, extra: str = "") -> None:
    """Print a status line for a model."""
    status_labels = {
        RunStatus.PENDING: "[PENDING] ",
        RunStatus.STARTED: "[STARTED] ",
        RunStatus.RECEIVING: "[RECEIVING]",
        RunStatus.COMPLETED: "[DONE]    ",
        RunStatus.FAILED: "[FAILED]  ",
        RunStatus.SKIPPED: "[SKIPPED] ",
    }
    label = status_labels.get(status, "[?]       ")
    suffix = f" {extra}" if extra else ""
    print(f"{label} {spec.display_name}{suffix}")


def run_sequential(
    specs: list[ModelSpec],
    puzzle_name: str,
) -> list[ModelRunResult]:
    """Run models one at a time in sequence."""
    results: list[ModelRunResult] = []

    for i, spec in enumerate(specs):
        print(f"\n[{i + 1}/{len(specs)}] Running {spec.display_name}...")
        result = run_single_model(spec, puzzle_name, quiet=False)
        results.append(result)

        if result.status == RunStatus.COMPLETED:
            print(f"  Completed in {result.duration_seconds:.1f}s")
        else:
            print(f"  Failed: {result.error}")

    return results


def run_parallel_by_provider(
    specs: list[ModelSpec],
    puzzle_name: str,
) -> list[ModelRunResult]:
    """Run one model at a time per provider (5 concurrent streams)."""
    # Group specs by runner_provider
    by_provider: dict[str, list[ModelSpec]] = defaultdict(list)
    for spec in specs:
        by_provider[spec.runner_provider].append(spec)

    all_results: list[ModelRunResult] = []
    results_lock = threading.Lock()
    print_lock = threading.Lock()

    def status_callback(spec: ModelSpec, status: RunStatus) -> None:
        with print_lock:
            _print_status(spec, status)

    def run_provider_queue(provider: str, queue: list[ModelSpec]) -> list[ModelRunResult]:
        """Run all models in a single provider's queue sequentially."""
        provider_results: list[ModelRunResult] = []
        for spec in queue:
            result = run_single_model(
                spec,
                puzzle_name,
                status_callback=status_callback,
                quiet=True,
            )
            with print_lock:
                if result.status == RunStatus.COMPLETED:
                    _print_status(spec, RunStatus.COMPLETED, f"({result.duration_seconds:.1f}s)")
                else:
                    _print_status(spec, RunStatus.FAILED, result.error or "")
            provider_results.append(result)
        return provider_results

    # Use ThreadPoolExecutor to run provider queues in parallel
    with ThreadPoolExecutor(max_workers=len(by_provider)) as executor:
        futures = {
            executor.submit(run_provider_queue, provider, queue): provider
            for provider, queue in by_provider.items()
        }

        for future in as_completed(futures):
            provider = futures[future]
            try:
                provider_results = future.result()
                with results_lock:
                    all_results.extend(provider_results)
            except Exception as e:
                with print_lock:
                    print(f"[ERROR] Provider {provider} failed: {e}")

    return all_results


def run_parallel_all(
    specs: list[ModelSpec],
    puzzle_name: str,
    max_workers: int = 30,
) -> list[ModelRunResult]:
    """Run all models in parallel (up to max_workers)."""
    all_results: list[ModelRunResult] = []
    results_lock = threading.Lock()
    print_lock = threading.Lock()

    def status_callback(spec: ModelSpec, status: RunStatus) -> None:
        with print_lock:
            _print_status(spec, status)

    def run_model(spec: ModelSpec) -> ModelRunResult:
        result = run_single_model(
            spec,
            puzzle_name,
            status_callback=status_callback,
            quiet=True,
        )
        with print_lock:
            if result.status == RunStatus.COMPLETED:
                _print_status(spec, RunStatus.COMPLETED, f"({result.duration_seconds:.1f}s)")
            else:
                _print_status(spec, RunStatus.FAILED, result.error or "")
        return result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_model, spec): spec for spec in specs}

        for future in as_completed(futures):
            spec = futures[future]
            try:
                result = future.result()
                with results_lock:
                    all_results.append(result)
            except Exception as e:
                with results_lock:
                    all_results.append(
                        ModelRunResult(
                            spec=spec,
                            status=RunStatus.FAILED,
                            error=str(e),
                        )
                    )

    return all_results


def print_summary(results: list[ModelRunResult], skipped_count: int = 0) -> None:
    """Print final summary of batch run."""
    completed = [r for r in results if r.status == RunStatus.COMPLETED]
    failed = [r for r in results if r.status == RunStatus.FAILED]

    total_duration = sum(r.duration_seconds for r in results)

    print("\n" + "=" * 60)
    print("BATCH RUN SUMMARY")
    print("=" * 60)
    print(f"Completed: {len(completed)}")
    print(f"Failed:    {len(failed)}")
    if skipped_count > 0:
        print(f"Skipped:   {skipped_count}  (resume mode)")
    print(f"Total:     {len(results) + skipped_count}")
    print(f"\nTotal Duration: {total_duration:.1f}s")

    if failed:
        print("\nFailed Models:")
        for r in failed:
            print(f"  - {r.spec.display_name}: {r.error}")


def run_batch(
    puzzle_name: str,
    puzzle_version: str | None,
    specs: list[ModelSpec],
    mode: ExecutionMode,
    responses_dir: Path,
    *,
    resume: bool = False,
    dry_run: bool = False,
) -> list[ModelRunResult]:
    """Main entry point for batch execution.

    Args:
        puzzle_name: Name of the puzzle to run
        puzzle_version: Version of the puzzle (for resume checking)
        specs: List of model specs to run
        mode: Execution mode
        responses_dir: Base directory for responses
        resume: If True, skip models with existing responses
        dry_run: If True, just print what would be run

    Returns:
        List of results from executed models
    """
    skipped_count = 0

    # Handle resume mode
    if resume:
        existing = find_existing_responses(puzzle_name, puzzle_version, responses_dir)
        specs_to_run = []
        for spec in specs:
            if (spec.provider, spec.model) in existing:
                print(f"[SKIPPED] {spec.display_name} - already has response")
                skipped_count += 1
            else:
                specs_to_run.append(spec)
        specs = specs_to_run

    if not specs:
        print("No models to run.")
        return []

    if dry_run:
        print(f"\nWould run {len(specs)} models:")
        for spec in specs:
            print(f"  - {spec.display_name} ({spec.provider}/{spec.model})")
        return []

    print(f"\nRunning {len(specs)} models in {mode.value} mode...")

    # Execute based on mode
    if mode == ExecutionMode.SEQUENTIAL:
        results = run_sequential(specs, puzzle_name)
    elif mode == ExecutionMode.PARALLEL_PROVIDER:
        results = run_parallel_by_provider(specs, puzzle_name)
    elif mode == ExecutionMode.PARALLEL_ALL:
        results = run_parallel_all(specs, puzzle_name)
    else:
        raise ValueError(f"Unknown execution mode: {mode}")

    # Print summary
    print_summary(results, skipped_count)

    return results
