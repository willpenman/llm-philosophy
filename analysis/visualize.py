"""Visualization of model embeddings as 2D scatter plots."""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from analysis.distances import ModelPoint


# Color palette for providers
PROVIDER_COLORS = {
    "anthropic": "#D97706",   # Amber/orange
    "openai": "#10B981",      # Green
    "gemini": "#3B82F6",      # Blue
    "grok": "#8B5CF6",        # Purple
    "deepseek": "#EF4444",    # Red
    "meta": "#06B6D4",        # Cyan
    "kimi": "#EC4899",        # Pink
    "qwen": "#F59E0B",        # Yellow-orange
}

# Display names for providers
PROVIDER_DISPLAY = {
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "gemini": "Google",
    "grok": "xAI",
    "deepseek": "DeepSeek",
    "meta": "Meta",
    "kimi": "Moonshot AI",
    "qwen": "Qwen",
}


def _shorten_claude_name(model: str) -> str | None:
    """Create a short display name for Claude models.

    Returns None if not a Claude model.

    Examples:
        claude-opus-4-7 -> Opus 4.7
        claude-opus-4-5-20251101 -> Opus 4.5
        claude-sonnet-4-6 -> Sonnet 4.6
        claude-opus-4-20250514 -> Opus 4
        claude-3-haiku-20240307 -> Haiku 3
    """
    lower = model.lower()

    # Guard: must start with "claude-"
    prefix = "claude-"
    if not lower.startswith(prefix):
        return None

    rest = lower[len(prefix):]

    # Handle Claude 3.x models (pattern: claude-3-{variant}-{date})
    if rest.startswith("3-"):
        for v in ("haiku", "sonnet", "opus"):
            if v in rest:
                return f"{v.capitalize()} 3"
        return None  # unrecognized Claude 3 model

    # Handle Claude 4.x+ models (pattern: claude-{variant}-{major}-{minor}[-date])
    # Identify variant
    variant = None
    for v in ("opus", "sonnet", "haiku"):
        if rest.startswith(v + "-"):
            variant = v.capitalize()
            rest = rest[len(v) + 1:]
            break

    if not variant:
        return None  # unrecognized pattern

    # Parse version: expect "4-7" or "4-5-20251101" or "4-20250514"
    parts = rest.split("-")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        major = parts[0]
        minor = parts[1]
        # Check if minor looks like a date (8 digits) vs actual minor version
        if len(minor) == 8:
            # It's a date, so this is like "4-20250514" meaning version 4.0
            return f"{variant} {major}"
        else:
            # It's a real minor version like "4-7" or "4-5"
            return f"{variant} {major}.{minor}"
    elif len(parts) >= 1 and parts[0].isdigit():
        # Just major version
        return f"{variant} {parts[0]}"

    return None  # unrecognized pattern


def _shorten_gpt_name(model: str) -> str | None:
    """Create a short display name for GPT models (GPT-4+).

    Returns None if not a GPT model or not handled.

    Examples:
        gpt-5.4-2026-03-05 -> GPT-5.4
        gpt-5.4-pro-2026-03-05 -> GPT-5.4 Pro
        gpt-5-2025-08-07 -> GPT-5
        gpt-4o-2024-05-13 -> GPT-4o
        gpt-4-0613 -> GPT-4
    """
    lower = model.lower()

    # Guard: must start with "gpt-"
    prefix = "gpt-"
    if not lower.startswith(prefix):
        return None

    rest = lower[len(prefix):]

    # Handle GPT-4o separately (special naming)
    if rest.startswith("4o"):
        return "GPT-4o"

    # Handle GPT-4 (old style: gpt-4-0613)
    if rest.startswith("4-") or rest == "4":
        return "GPT-4"

    # Handle GPT-5+ models
    # Pattern: {version}[-variant][-date] where version is like "5" or "5.4"
    # Examples: 5.4-2026-03-05, 5.4-pro-2026-03-05, 5-2025-08-07

    parts = rest.split("-")
    if not parts:
        return None

    # First part should be version (e.g., "5", "5.4")
    version = parts[0]
    if not version[0].isdigit():
        return None

    # Check for variant (pro, mini, nano, etc.) - it's not a date
    variant = ""
    for part in parts[1:]:
        # Dates are 4 digits (year) or 8 digits (YYYYMMDD) or 10 chars (YYYY-MM-DD parts)
        if part.isdigit() and len(part) >= 4:
            break  # hit a date component
        if part in ("pro", "mini", "nano"):
            variant = f" {part.capitalize()}"
            break

    return f"GPT-{version}{variant}"


def _shorten_model_name(model: str) -> str:
    """Create a short display name for a model."""
    # Try provider-specific handling first
    claude_name = _shorten_claude_name(model)
    if claude_name:
        return claude_name

    gpt_name = _shorten_gpt_name(model)
    if gpt_name:
        return gpt_name

    # Common patterns to shorten (order matters - more specific first)
    replacements = [
        ("o3-2025-04-16", "o3"),
        ("o3-", "o3 "),
        ("gemini-3.1-pro-preview", "Gemini 3.1 Pro"),
        ("gemini-3-pro-preview", "Gemini 3 Pro"),
        ("gemini-3.1-pro", "Gemini 3.1 Pro"),
        ("gemini-3-pro", "Gemini 3 Pro"),
        ("gemini-2.5-pro", "Gemini 2.5 Pro"),
        ("gemini-2.0-flash-lite-001", "Flash Lite"),
        ("gemini-2.0-flash-lite", "Flash Lite"),
        ("gemini-", "Gemini "),
        ("grok-4-1-fast-reasoning", "Grok 4.1"),
        ("grok-2-vision-1212", "Grok 2"),
        ("grok-3", "Grok 3"),
        ("grok-2-vision", "Grok 2"),
        ("grok-", "Grok "),
        ("deepseek-v3p2", "DS 3.2"),
        ("deepseek-v3p1", "DS 3.1"),
        ("deepseek-", "DeepSeek "),
        ("llama-v3p3-70b-instruct", "Llama 3.3 70B"),
        ("llama-", "Llama "),
        ("kimi-k2p5", "K2.5"),
        ("kimi-k2-instruct-0905", "K2"),
        ("kimi-k2-instruct", "K2"),
        ("kimi-", "Kimi "),
        ("qwen3-vl-235b-thinking", "Qwen3-VL 235B"),
        ("qwen2p5-vl-32b", "Qwen2.5-VL 32B"),
        ("-preview", ""),
        ("-001", ""),
    ]

    result = model.lower()
    for old, new in replacements:
        if old.lower() in result:
            result = result.replace(old.lower(), new)
            break

    return result.strip()


def _add_radial_labels(
    ax: plt.Axes,
    points: list[ModelPoint],
    label_distance: float = 0.08,
) -> None:
    """Add labels positioned radially outward from the centroid.

    Args:
        ax: Matplotlib axes
        points: List of ModelPoint objects
        label_distance: Distance to push labels outward from points
    """
    if not points:
        return

    # Compute centroid
    cx = np.mean([p.x for p in points])
    cy = np.mean([p.y for p in points])

    for point in points:
        label = _shorten_model_name(point.model)

        # Vector from centroid to point
        dx = point.x - cx
        dy = point.y - cy
        dist = np.sqrt(dx**2 + dy**2)

        if dist > 0:
            # Normalize and extend
            dx_norm = dx / dist
            dy_norm = dy / dist
        else:
            # Point is at centroid, default to right
            dx_norm, dy_norm = 1, 0

        # Label position: push outward from point
        label_x = point.x + dx_norm * label_distance
        label_y = point.y + dy_norm * label_distance

        # Determine text alignment based on direction
        if dx_norm > 0.3:
            ha = "left"
        elif dx_norm < -0.3:
            ha = "right"
        else:
            ha = "center"

        if dy_norm > 0.3:
            va = "bottom"
        elif dy_norm < -0.3:
            va = "top"
        else:
            va = "center"

        # Add label
        ax.text(
            label_x, label_y, label,
            fontsize=8, alpha=0.9,
            ha=ha, va=va,
        )


def plot_model_map(
    points: list[ModelPoint],
    title: str,
    output_path: Path | None = None,
    figsize: tuple[float, float] = (10, 8),
    show_legend: bool = True,
    subtitle: str | None = None,
) -> plt.Figure:
    """Create a 2D scatter plot of model positions.

    Args:
        points: List of ModelPoint objects
        title: Plot title
        output_path: Optional path to save PNG
        figsize: Figure size in inches
        show_legend: Whether to show provider legend
        subtitle: Optional subtitle (e.g., spread statistics)

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Group by provider for legend
    providers_seen = set()

    for point in points:
        color = PROVIDER_COLORS.get(point.provider, "#6B7280")
        providers_seen.add(point.provider)

        ax.scatter(
            point.x, point.y,
            c=color,
            s=100,
            alpha=0.8,
            edgecolors="white",
            linewidth=1,
        )

        # Add label
        label = _shorten_model_name(point.model)
        ax.annotate(
            label,
            (point.x, point.y),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            alpha=0.9,
        )

    # Legend
    if show_legend and providers_seen:
        handles = []
        for provider in sorted(providers_seen):
            color = PROVIDER_COLORS.get(provider, "#6B7280")
            display = PROVIDER_DISPLAY.get(provider, provider.title())
            patch = mpatches.Patch(color=color, label=display)
            handles.append(patch)
        ax.legend(handles=handles, loc="upper right", framealpha=0.9)

    # Title
    if subtitle:
        ax.set_title(f"{title}\n{subtitle}", fontsize=12)
    else:
        ax.set_title(title, fontsize=14)

    # Clean up axes
    ax.set_xlabel("Dimension 1")
    ax.set_ylabel("Dimension 2")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="datalim")

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_path}")

    return fig


def plot_comparison(
    baseline_points: list[ModelPoint],
    philosophy_points: list[ModelPoint],
    output_path: Path | None = None,
    figsize: tuple[float, float] = (18, 7),
    baseline_title: str = "Baseline Opinions",
    philosophy_title: str = "Philosophy Positions",
    baseline_spread: float | None = None,
    philosophy_spread: float | None = None,
) -> plt.Figure:
    """Create side-by-side comparison of philosophy and baseline maps.

    Args:
        baseline_points: Points from baseline tasks
        philosophy_points: Points from philosophy puzzles
        output_path: Optional path to save PNG
        figsize: Figure size
        baseline_title: Title for baseline subplot
        philosophy_title: Title for philosophy subplot
        baseline_spread: Optional spread statistic for baseline (unused)
        philosophy_spread: Optional spread statistic for philosophy (unused)

    Returns:
        matplotlib Figure object
    """
    # Create 3 subplots: philosophy, legend area, baseline
    fig, (ax1, ax_legend, ax2) = plt.subplots(
        1, 3, figsize=figsize,
        gridspec_kw={"width_ratios": [1, 0.15, 1]}
    )

    # Compute shared axis limits for fair comparison
    all_points = baseline_points + philosophy_points
    if all_points:
        all_x = [p.x for p in all_points]
        all_y = [p.y for p in all_points]
        margin = 0.1
        x_range = max(all_x) - min(all_x)
        y_range = max(all_y) - min(all_y)
        xlim = (min(all_x) - margin * x_range, max(all_x) + margin * x_range)
        ylim = (min(all_y) - margin * y_range, max(all_y) + margin * y_range)
    else:
        xlim = (-1, 1)
        ylim = (-1, 1)

    providers_seen = set()

    # Plot philosophy points (first/left)
    for point in philosophy_points:
        color = PROVIDER_COLORS.get(point.provider, "#6B7280")
        providers_seen.add(point.provider)
        ax1.scatter(point.x, point.y, c=color, s=100, alpha=0.8,
                    edgecolors="white", linewidth=1)

    # Add radial labels for philosophy
    _add_radial_labels(ax1, philosophy_points, label_distance=0.01)

    ax1.set_title(philosophy_title)
    ax1.set_xlim(xlim)
    ax1.set_ylim(ylim)
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect("equal", adjustable="box")

    # Plot baseline points (second/right)
    for point in baseline_points:
        color = PROVIDER_COLORS.get(point.provider, "#6B7280")
        providers_seen.add(point.provider)
        ax2.scatter(point.x, point.y, c=color, s=100, alpha=0.8,
                    edgecolors="white", linewidth=1)

    # Add radial labels for baseline
    _add_radial_labels(ax2, baseline_points, label_distance=0.01)

    ax2.set_title(baseline_title)
    ax2.set_xlim(xlim)
    ax2.set_ylim(ylim)
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect("equal", adjustable="box")

    # Legend in center column
    ax_legend.axis("off")
    if providers_seen:
        handles = []
        for provider in sorted(providers_seen):
            color = PROVIDER_COLORS.get(provider, "#6B7280")
            display = PROVIDER_DISPLAY.get(provider, provider.title())
            patch = mpatches.Patch(color=color, label=display)
            handles.append(patch)
        ax_legend.legend(
            handles=handles, loc="center", framealpha=0.9,
            fontsize=10, title="Provider"
        )

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_path}")

    return fig
