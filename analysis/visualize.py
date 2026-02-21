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


def _shorten_model_name(model: str) -> str:
    """Create a short display name for a model."""
    # Common patterns to shorten
    replacements = [
        ("claude-opus-", "Opus "),
        ("claude-sonnet-", "Sonnet "),
        ("claude-haiku-", "Haiku "),
        ("claude-", "Claude "),
        ("gpt-5.2-pro", "GPT-5.2 Pro"),
        ("gpt-5.2", "GPT-5.2"),
        ("gpt-4o-", "GPT-4o "),
        ("gpt-4-", "GPT-4 "),
        ("o3-", "o3 "),
        ("gemini-3.1-pro", "Gemini 3.1 Pro"),
        ("gemini-3-pro", "Gemini 3 Pro"),
        ("gemini-2.0-flash-lite", "Gemini Flash Lite"),
        ("gemini-", "Gemini "),
        ("grok-4-1-fast-reasoning", "Grok 4.1"),
        ("grok-3", "Grok 3"),
        ("grok-2-vision", "Grok 2"),
        ("grok-", "Grok "),
        ("deepseek-v3p2", "V3.2"),
        ("deepseek-v3p1", "V3.1"),
        ("deepseek-", "DeepSeek "),
        ("llama-v3p3-70b-instruct", "Llama 3.3 70B"),
        ("llama-", "Llama "),
        ("kimi-k2p5", "K2.5"),
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
    figsize: tuple[float, float] = (16, 7),
    baseline_title: str = "Baseline Tasks",
    philosophy_title: str = "Philosophy Puzzles",
    baseline_spread: float | None = None,
    philosophy_spread: float | None = None,
) -> plt.Figure:
    """Create side-by-side comparison of baseline and philosophy maps.

    Args:
        baseline_points: Points from baseline tasks
        philosophy_points: Points from philosophy puzzles
        output_path: Optional path to save PNG
        figsize: Figure size
        baseline_title: Title for baseline subplot
        philosophy_title: Title for philosophy subplot
        baseline_spread: Optional spread statistic for baseline
        philosophy_spread: Optional spread statistic for philosophy

    Returns:
        matplotlib Figure object
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

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

    # Plot baseline
    for point in baseline_points:
        color = PROVIDER_COLORS.get(point.provider, "#6B7280")
        providers_seen.add(point.provider)
        ax1.scatter(point.x, point.y, c=color, s=100, alpha=0.8,
                    edgecolors="white", linewidth=1)
        label = _shorten_model_name(point.model)
        ax1.annotate(label, (point.x, point.y), xytext=(5, 5),
                     textcoords="offset points", fontsize=8, alpha=0.9)

    subtitle1 = f"(spread: {baseline_spread:.4f})" if baseline_spread is not None else ""
    ax1.set_title(f"{baseline_title}\n{subtitle1}" if subtitle1 else baseline_title)
    ax1.set_xlim(xlim)
    ax1.set_ylim(ylim)
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect("equal", adjustable="datalim")

    # Plot philosophy
    for point in philosophy_points:
        color = PROVIDER_COLORS.get(point.provider, "#6B7280")
        providers_seen.add(point.provider)
        ax2.scatter(point.x, point.y, c=color, s=100, alpha=0.8,
                    edgecolors="white", linewidth=1)
        label = _shorten_model_name(point.model)
        ax2.annotate(label, (point.x, point.y), xytext=(5, 5),
                     textcoords="offset points", fontsize=8, alpha=0.9)

    subtitle2 = f"(spread: {philosophy_spread:.4f})" if philosophy_spread is not None else ""
    ax2.set_title(f"{philosophy_title}\n{subtitle2}" if subtitle2 else philosophy_title)
    ax2.set_xlim(xlim)
    ax2.set_ylim(ylim)
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect("equal", adjustable="datalim")

    # Shared legend
    if providers_seen:
        handles = []
        for provider in sorted(providers_seen):
            color = PROVIDER_COLORS.get(provider, "#6B7280")
            display = PROVIDER_DISPLAY.get(provider, provider.title())
            patch = mpatches.Patch(color=color, label=display)
            handles.append(patch)
        fig.legend(handles=handles, loc="center right", framealpha=0.9)

    plt.tight_layout()
    plt.subplots_adjust(right=0.88)  # Make room for legend

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_path}")

    return fig
