"""In-place updating display for parallel batch runs."""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.batch_runner import ModelSpec, RunStatus


class DisplayStatus(Enum):
    """Display status for a model in the progress display."""

    PENDING = "pending"  # · (queued, waiting its turn)
    REQUESTED = "requested"  # * (HTTP sent, awaiting response)
    STREAMING = "streaming"  # ◉ (actively receiving data)
    COMPLETED = "completed"  # ✓
    FAILED = "failed"  # ✗


# Symbol mapping
SYMBOLS = {
    DisplayStatus.PENDING: "·",
    DisplayStatus.REQUESTED: "*",
    DisplayStatus.STREAMING: "◉",
    DisplayStatus.COMPLETED: "✓",
    DisplayStatus.FAILED: "✗",
}

# Max provider name length + 1 space (Fireworks = 9 chars).
# If we add a longer provider name in the future, update this width.
PROVIDER_NAME_WIDTH = 10


@dataclass
class ModelState:
    """Tracks state of a single model."""

    spec: "ModelSpec"
    status: DisplayStatus = DisplayStatus.PENDING


@dataclass
class ProviderState:
    """Tracks state of all models for a provider."""

    name: str
    display_name: str
    models: list[ModelState] = field(default_factory=list)
    current_model: str | None = None  # For parallel-provider "Now:" display


class BatchDisplayManager:
    """In-place updating display for parallel batch runs.

    Provides a calm, monochrome progress display that updates in place.
    Shows provider rows with status symbols and optional "Now:" indicators.
    """

    def __init__(
        self,
        specs: list["ModelSpec"],
        puzzle_name: str,
        skipped_models: list[str] | None = None,
        skipped_message: str | None = None,
        show_current_model: bool = True,  # False for parallel-all
    ) -> None:
        """Initialize the display manager.

        Args:
            specs: List of ModelSpec to track (excludes skipped models)
            puzzle_name: Name of the puzzle being run
            skipped_models: Display names of models that were skipped (resume mode)
            show_current_model: Whether to show "Now:" indicator (False for parallel-all)
        """
        self._puzzle_name = puzzle_name
        self._skipped_models = skipped_models or []
        self._skipped_message = skipped_message
        self._show_current = show_current_model
        self._lock = threading.Lock()
        self._line_count = 0  # Track lines for cursor movement
        self._is_tty = sys.stdout.isatty()
        self._errors: list[tuple[str, str]] = []  # (model_name, error_msg)
        self._started = False
        self._symbols_width = 0

        # Group specs by runner_provider, sorted alphabetically
        self._providers: dict[str, ProviderState] = {}
        self._spec_to_state: dict[tuple[str, str], ModelState] = {}

        for spec in specs:
            provider_key = spec.runner_provider
            if provider_key not in self._providers:
                # Use a nicer display name for the provider
                display_name = self._provider_display_name(provider_key)
                self._providers[provider_key] = ProviderState(
                    name=provider_key,
                    display_name=display_name,
                )
            state = ModelState(spec=spec)
            self._providers[provider_key].models.append(state)
            self._spec_to_state[(spec.provider, spec.model)] = state

        max_models = max((len(p.models) for p in self._providers.values()), default=0)
        if max_models > 0:
            self._symbols_width = max_models * 2 - 1

    def _provider_display_name(self, runner_provider: str) -> str:
        """Convert runner_provider to display name."""
        names = {
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "gemini": "Gemini",
            "grok": "xAI",
            "fireworks": "Fireworks",
        }
        return names.get(runner_provider, runner_provider.title())

    def start(self) -> None:
        """Print initial display. Call before any updates."""
        with self._lock:
            self._started = True
            self._print_initial()

    def _print_initial(self) -> None:
        """Print initial state. Must hold _lock."""
        lines: list[str] = []

        # Puzzle header
        lines.append(f"Puzzle: {self._puzzle_name}")

        # Skipped models (if any)
        if self._skipped_message:
            lines.append(self._skipped_message)

        lines.append("")  # Blank line before providers

        # Provider rows
        for provider_key in sorted(self._providers.keys()):
            provider = self._providers[provider_key]
            line = self._format_provider_line(provider)
            lines.append(line)

        lines.append("")  # Blank line before summary

        # Summary line
        completed = self._count_completed()
        total = self._count_total()
        lines.append(f"Received {completed}/{total} responses")

        # Print all lines
        output = "\n".join(lines)
        print(output, flush=True)
        self._line_count = len(lines)

    def _format_provider_line(self, provider: ProviderState) -> str:
        """Format a single provider line with symbols."""
        # Pad provider name to a fixed width for alignment
        name_col = f"{provider.display_name:<{PROVIDER_NAME_WIDTH}}"

        # Build symbol string: completed first, then in-flight, then pending
        completed_symbols: list[str] = []
        inflight_symbols: list[str] = []
        pending_symbols: list[str] = []

        for model_state in provider.models:
            symbol = SYMBOLS[model_state.status]
            if model_state.status in (DisplayStatus.COMPLETED, DisplayStatus.FAILED):
                completed_symbols.append(symbol)
            elif model_state.status in (DisplayStatus.REQUESTED, DisplayStatus.STREAMING):
                inflight_symbols.append(symbol)
            else:
                pending_symbols.append(symbol)

        all_symbols = completed_symbols + inflight_symbols + pending_symbols
        symbols_str = " ".join(all_symbols)
        if self._symbols_width > 0:
            symbols_str = symbols_str.ljust(self._symbols_width)

        # Add "Now:" indicator if showing current model
        if self._show_current and provider.current_model:
            # Check if it's a Grok model (non-streaming)
            is_grok = provider.name == "grok"
            suffix = " (non-streaming)" if is_grok else ""
            now_str = f"     Now: {provider.current_model}{suffix}"
            return f"{name_col}{symbols_str}{now_str}"

        return f"{name_col}{symbols_str}"

    def _count_completed(self) -> int:
        """Count completed (success + failed) models."""
        count = 0
        for provider in self._providers.values():
            for model_state in provider.models:
                if model_state.status in (DisplayStatus.COMPLETED, DisplayStatus.FAILED):
                    count += 1
        return count

    def _count_total(self) -> int:
        """Count total models being tracked."""
        return sum(len(p.models) for p in self._providers.values())

    def _count_failed(self) -> int:
        """Count failed models."""
        count = 0
        for provider in self._providers.values():
            for model_state in provider.models:
                if model_state.status == DisplayStatus.FAILED:
                    count += 1
        return count

    def update(
        self,
        spec: "ModelSpec",
        status: "RunStatus",
        error: str | None = None,
    ) -> None:
        """Update model status. Thread-safe.

        Args:
            spec: The model spec being updated
            status: New RunStatus from batch_runner
            error: Error message if status is FAILED
        """
        # Import here to avoid circular imports
        from src.batch_runner import RunStatus

        with self._lock:
            key = (spec.provider, spec.model)
            if key not in self._spec_to_state:
                return  # Unknown model, ignore

            model_state = self._spec_to_state[key]
            provider = self._providers[spec.runner_provider]

            # Map RunStatus -> DisplayStatus
            if status == RunStatus.STARTED:
                model_state.status = DisplayStatus.REQUESTED
                provider.current_model = spec.display_name
            elif status == RunStatus.RECEIVING:
                if model_state.status not in (
                    DisplayStatus.COMPLETED,
                    DisplayStatus.FAILED,
                ):
                    model_state.status = DisplayStatus.STREAMING
                    provider.current_model = spec.display_name
            elif status == RunStatus.COMPLETED:
                model_state.status = DisplayStatus.COMPLETED
                provider.current_model = None
            elif status == RunStatus.FAILED:
                model_state.status = DisplayStatus.FAILED
                provider.current_model = None
                if error:
                    self._errors.append((spec.display_name, error))

            self._redraw()

    def _redraw(self) -> None:
        """Clear and redraw the entire display. Must hold _lock."""
        if not self._is_tty or not self._started:
            return  # Fall back to simple output or not started yet

        # Move cursor up to beginning of our output
        if self._line_count > 0:
            sys.stdout.write(f"\033[{self._line_count}F")

        lines: list[str] = []

        # Puzzle header
        lines.append(f"Puzzle: {self._puzzle_name}")

        # Skipped models (if any)
        if self._skipped_message:
            lines.append("")

        lines.append("")  # Blank line before providers

        # Provider rows
        for provider_key in sorted(self._providers.keys()):
            provider = self._providers[provider_key]
            line = self._format_provider_line(provider)
            lines.append(line)

        lines.append("")  # Blank line before summary

        # Summary line
        completed = self._count_completed()
        total = self._count_total()
        lines.append(f"Received {completed}/{total} responses")

        # Print each line, clearing to end of line
        for line in lines:
            sys.stdout.write(f"\033[K{line}\n")

        sys.stdout.flush()
        self._line_count = len(lines)

    def finalize(self, total_cost: float | None = None) -> None:
        """Print final summary after all models complete.

        Args:
            total_cost: Aggregated cost in dollars (optional)
        """
        with self._lock:
            if not self._is_tty:
                # Simple output for non-TTY
                completed = self._count_completed()
                total = self._count_total()
                failed = self._count_failed()
                if failed > 0:
                    print(f"Completed {completed}/{total} ({failed} failed)")
                else:
                    print(f"Completed {completed}/{total}")
                if total_cost is not None:
                    print(f"Total cost: ${total_cost:.2f}")
                if self._errors:
                    print("\nErrors:")
                    for model_name, error_msg in self._errors:
                        print(f"  {model_name}: {error_msg}")
                return

            # TTY mode: redraw final state
            if self._line_count > 0:
                sys.stdout.write(f"\033[{self._line_count}F")

            lines: list[str] = []

            # Puzzle header (no skipped line in final output)
            lines.append(f"Puzzle: {self._puzzle_name}")
            lines.append("")

            # Provider rows (final state, no "Now:" indicators)
            for provider_key in sorted(self._providers.keys()):
                provider = self._providers[provider_key]
                # Format without current_model for final state
                name_col = f"{provider.display_name:<{PROVIDER_NAME_WIDTH}}"
                symbols = [SYMBOLS[m.status] for m in provider.models]
                symbols_str = " ".join(symbols)
                if self._symbols_width > 0:
                    symbols_str = symbols_str.ljust(self._symbols_width)
                lines.append(f"{name_col}{symbols_str}")

            lines.append("")

            # Final summary
            completed = self._count_completed()
            total = self._count_total()
            failed = self._count_failed()
            if failed > 0:
                lines.append(f"Completed {completed}/{total} ({failed} failed)")
            else:
                lines.append(f"Completed {completed}/{total}")

            if total_cost is not None:
                lines.append(f"Total cost: ${total_cost:.2f}")

            # Print lines, clearing each
            for line in lines:
                sys.stdout.write(f"\033[K{line}\n")

            # Print errors below (not part of redrawn area)
            if self._errors:
                print("\nErrors:")
                for model_name, error_msg in self._errors:
                    print(f"  {model_name}: {error_msg}")

            sys.stdout.flush()


def aggregate_costs(results: list) -> float | None:
    """Aggregate costs from a list of ModelRunResult.

    Args:
        results: List of ModelRunResult from batch run

    Returns:
        Total cost in dollars, or None if no cost data available
    """
    total = 0.0
    has_cost = False
    for r in results:
        if r.run_result and r.run_result.cost:
            total += r.run_result.cost.total_cost
            has_cost = True
    return total if has_cost else None
