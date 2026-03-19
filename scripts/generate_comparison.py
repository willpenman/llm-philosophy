"""Generate model similarity visualizations.

Usage:
    # When adding a model, recompute points (shared cache for both modes)
    python -m scripts.generate_comparison philosophy_all --recompute-points
    
    # Side-by-side comparison of baseline vs few-puzzle philosophy responses
    python -m scripts.generate_comparison panopticon
    python -m scripts.generate_comparison panopticon sapir_whorf  # multiple puzzles

    # Philosophy-only mode (no baseline comparison, no rescaling)
    python -m scripts.generate_comparison panopticon --philosophy-only
    python -m scripts.generate_comparison panopticon sapir_whorf --philosophy-only

    # Emit all three standard plots for a new puzzle
    python -m scripts.generate_comparison panopticon --emit-all

    # Custom output path
    python -m scripts.generate_comparison panopticon --output analysis/figures/custom.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from analysis.embeddings import (
    embed_baseline_responses_by_prompt,
    embed_puzzle_responses_by_puzzle,
)
from analysis.distances import (
    CachedPoints,
    compute_averaged_distance_matrix,
    project_to_2d,
    compute_spread,
    compute_mean_pairwise_distance,
    compute_mean_pairwise_distance_points,
    scale_points,
    save_points,
    load_points,
)
from analysis.visualize import plot_comparison, plot_model_map


ROOT = Path(__file__).resolve().parents[1]
RESPONSES_DIR = ROOT / "responses"
BASELINES_DIR = ROOT / "baselines" / "responses"
CACHE_DIR = ROOT / "analysis" / "embeddings"
FIGURES_DIR = ROOT / "analysis" / "figures"


def _display_title(puzzle_slug: str) -> str:
    if puzzle_slug == "philosophy_all":
        return "Model Similarity: All Philosophy Puzzles"
    return f"Model Similarity: {puzzle_slug.replace('_', ' ').title()}"


def _load_or_compute_points(
    slug: str,
    embed_fn: callable,
    cache_dir: Path | None,
    recompute: bool,
) -> CachedPoints | None:
    """Load cached points or compute fresh ones.

    Args:
        slug: Cache key (e.g., "baseline" or "philosophy_all")
        embed_fn: Function that returns per-task embeddings dict
        cache_dir: Directory for embedding cache (None to skip)
        recompute: If True, ignore cached points and recompute

    Returns:
        CachedPoints with unscaled MDS projection, or None if no data
    """
    points_cache = CACHE_DIR / f"points_{slug}.json"

    if not recompute:
        cached = load_points(points_cache)
        if cached is not None:
            print(f"Using cached points for {slug} (use --recompute-points to regenerate)")
            return cached

    # Compute fresh embeddings and project
    embeddings_by_task = embed_fn(cache_dir)
    if not embeddings_by_task:
        return None

    distances, keys = compute_averaged_distance_matrix(embeddings_by_task)
    mean_dist = compute_mean_pairwise_distance(distances)
    points = project_to_2d(distances, keys)

    # Cache unscaled points with mean distance for later scaling
    save_points(points, points_cache, mean_cosine_distance=mean_dist)
    print(f"Cached points to {points_cache}")

    return CachedPoints(points=points, mean_cosine_distance=mean_dist)


def _run_philosophy_only(
    puzzle_names: list[str],
    puzzle_slug: str,
    output_path: Path,
    cache_dir: Path | None,
    recompute_points: bool,
    show: bool,
) -> None:
    """Generate philosophy-only map without baseline comparison.

    Filters to models that have both baseline and philosophy responses
    (same as comparison mode) so the results are directly comparable.
    No rescaling is applied since there's no baseline to match.
    """
    # Check for cached points first to avoid loading embeddings unnecessarily
    philosophy_points_cache = CACHE_DIR / f"points_{puzzle_slug}.json"

    if not recompute_points:
        cached = load_points(philosophy_points_cache)
        if cached is not None:
            print("Using cached points (use --recompute-points to regenerate)")
            _render_philosophy_only(cached, puzzle_slug, output_path, show)
            return

    # Need to compute points - load embeddings
    print("Loading baseline responses (for model filtering)...")
    baseline_by_prompt = embed_baseline_responses_by_prompt(
        baselines_dir=BASELINES_DIR,
        cache_dir=cache_dir,
    )

    baseline_models: set[tuple[str, str]] = set()
    for prompt_embeddings in baseline_by_prompt.values():
        baseline_models.update(prompt_embeddings.keys())

    # Define embedding function that filters to common models
    def get_philosophy_embeddings(cache_dir: Path | None) -> dict:
        philosophy_by_puzzle = embed_puzzle_responses_by_puzzle(
            responses_dir=RESPONSES_DIR,
            puzzle_names=puzzle_names,
            cache_dir=cache_dir,
        )
        if not philosophy_by_puzzle:
            return {}

        # Find common models
        philosophy_models: set[tuple[str, str]] = set()
        for puzzle_embeddings in philosophy_by_puzzle.values():
            philosophy_models.update(puzzle_embeddings.keys())

        common_models = baseline_models & philosophy_models
        print(f"Found {len(philosophy_models)} models, {len(common_models)} have baseline responses")

        if len(common_models) < 2:
            print("Need at least 2 common models for visualization.")
            return {}

        return {
            puzzle: {k: v for k, v in emb.items() if k in common_models}
            for puzzle, emb in philosophy_by_puzzle.items()
        }

    cached = _load_or_compute_points(
        slug=puzzle_slug,
        embed_fn=get_philosophy_embeddings,
        cache_dir=cache_dir,
        recompute=recompute_points,
    )

    if cached is None:
        print(f"No philosophy responses found for puzzles: {puzzle_names}")
        return

    _render_philosophy_only(cached, puzzle_slug, output_path, show)


def _render_philosophy_only(
    cached: CachedPoints,
    puzzle_slug: str,
    output_path: Path,
    show: bool,
) -> None:
    """Render the philosophy-only plot from cached points."""
    points = cached.points
    spread = compute_spread(points)
    mean_dist = cached.mean_cosine_distance

    print(f"Mean cosine distance: {mean_dist:.4f}, Spread: {spread:.4f}")

    # Generate plot
    title = _display_title(puzzle_slug)
    subtitle = f"Mean distance: {mean_dist:.4f}, Spread: {spread:.4f}"

    fig = plot_model_map(
        points=points,
        title=title,
        subtitle=subtitle,
        output_path=output_path,
    )

    if show:
        import matplotlib.pyplot as plt
        plt.show()

    print("\nDone!")


def _compute_scale_factor(cached: CachedPoints) -> float:
    """Compute scale factor to make 2D distances match cosine distances."""
    if not cached.points or cached.mean_cosine_distance == 0:
        return 1.0

    points_mean = compute_mean_pairwise_distance_points(cached.points)
    if points_mean == 0:
        return 1.0

    return cached.mean_cosine_distance / points_mean


def _run_comparison(
    puzzle_names: list[str],
    puzzle_slug: str,
    output_path: Path,
    cache_dir: Path | None,
    recompute_points: bool,
    show: bool,
) -> None:
    """Generate baseline vs philosophy comparison plot."""
    # Check for cached points first to avoid loading embeddings unnecessarily
    baseline_points_cache = CACHE_DIR / "points_baseline.json"
    philosophy_points_cache = CACHE_DIR / f"points_{puzzle_slug}.json"

    if not recompute_points:
        baseline_cached = load_points(baseline_points_cache)
        philosophy_cached = load_points(philosophy_points_cache)

        if baseline_cached is not None and philosophy_cached is not None:
            print("Using cached points (use --recompute-points to regenerate)")
            _render_comparison(
                baseline_cached, philosophy_cached, puzzle_slug, output_path, show
            )
            return

    # Need to compute at least one set of points - load embeddings
    print("Loading baseline responses (per-prompt)...")
    baseline_by_prompt = embed_baseline_responses_by_prompt(
        baselines_dir=BASELINES_DIR,
        cache_dir=cache_dir,
    )

    if not baseline_by_prompt:
        print("No baseline responses found. Run `python -m scripts.run_baselines --model ALL` first.")
        return

    baseline_models: set[tuple[str, str]] = set()
    for prompt_embeddings in baseline_by_prompt.values():
        baseline_models.update(prompt_embeddings.keys())

    print(f"Found {len(baseline_models)} models across {len(baseline_by_prompt)} baseline prompts")

    # Define embedding functions that filter to common models
    def get_baseline_embeddings(cache_dir: Path | None) -> dict:
        # Re-use already loaded embeddings, filter to common models
        philosophy_by_puzzle = embed_puzzle_responses_by_puzzle(
            responses_dir=RESPONSES_DIR,
            puzzle_names=puzzle_names,
            cache_dir=cache_dir,
        )
        philosophy_models: set[tuple[str, str]] = set()
        for puzzle_embeddings in philosophy_by_puzzle.values():
            philosophy_models.update(puzzle_embeddings.keys())

        common_models = baseline_models & philosophy_models
        # NOTE: We filter to the intersection of baseline and philosophy responses. This
        # discards models that have philosophy responses but no baseline (or vice versa).
        # This is a conservative choice: we have more data than we use here, but averaging
        # distances across incomplete pairings is not well-defined mathematically.
        print(f"{len(common_models)} models have both baseline and philosophy responses")

        if len(common_models) < 2:
            print("Need at least 2 common models for comparison.")
            return {}

        return {
            prompt: {k: v for k, v in emb.items() if k in common_models}
            for prompt, emb in baseline_by_prompt.items()
        }

    def get_philosophy_embeddings(cache_dir: Path | None) -> dict:
        philosophy_by_puzzle = embed_puzzle_responses_by_puzzle(
            responses_dir=RESPONSES_DIR,
            puzzle_names=puzzle_names,
            cache_dir=cache_dir,
        )
        if not philosophy_by_puzzle:
            return {}

        philosophy_models: set[tuple[str, str]] = set()
        for puzzle_embeddings in philosophy_by_puzzle.values():
            philosophy_models.update(puzzle_embeddings.keys())

        common_models = baseline_models & philosophy_models
        print(f"Found {len(philosophy_models)} models, {len(common_models)} have baseline responses")

        if len(common_models) < 2:
            return {}

        return {
            puzzle: {k: v for k, v in emb.items() if k in common_models}
            for puzzle, emb in philosophy_by_puzzle.items()
        }

    # Load or compute points
    baseline_cached = _load_or_compute_points(
        slug="baseline",
        embed_fn=get_baseline_embeddings,
        cache_dir=cache_dir,
        recompute=recompute_points,
    )

    philosophy_cached = _load_or_compute_points(
        slug=puzzle_slug,
        embed_fn=get_philosophy_embeddings,
        cache_dir=cache_dir,
        recompute=recompute_points,
    )

    if baseline_cached is None:
        print("Failed to compute baseline points.")
        return

    if philosophy_cached is None:
        print(f"No philosophy responses found for puzzles: {puzzle_names}")
        return

    _render_comparison(baseline_cached, philosophy_cached, puzzle_slug, output_path, show)


def _render_comparison(
    baseline_cached: CachedPoints,
    philosophy_cached: CachedPoints,
    puzzle_slug: str,
    output_path: Path,
    show: bool,
) -> None:
    """Render the comparison plot from cached points."""
    # Apply scaling for visual comparison - use baseline's scale for both
    # so that visual distances are comparable across the two plots
    baseline_scale = _compute_scale_factor(baseline_cached)
    baseline_points = scale_points(baseline_cached.points, baseline_scale)
    philosophy_points = scale_points(philosophy_cached.points, baseline_scale)

    baseline_spread = compute_spread(baseline_points)
    philosophy_spread = compute_spread(philosophy_points)

    print(f"\nBaseline: mean distance = {baseline_cached.mean_cosine_distance:.4f}, spread = {baseline_spread:.4f}")
    print(f"Philosophy: mean distance = {philosophy_cached.mean_cosine_distance:.4f}, spread = {philosophy_spread:.4f}")

    # Compare
    if baseline_cached.mean_cosine_distance > 0:
        ratio = philosophy_cached.mean_cosine_distance / baseline_cached.mean_cosine_distance
        print(f"\nPhilosophy differentiation is {ratio:.2f}x baseline")

    philosophy_title = (
        "Philosophy Positions (All Puzzles)"
        if puzzle_slug == "philosophy_all"
        else "Philosophy Positions"
    )

    # Generate plot
    fig = plot_comparison(
        baseline_points=baseline_points,
        philosophy_points=philosophy_points,
        output_path=output_path,
        philosophy_title=philosophy_title,
    )

    if show:
        import matplotlib.pyplot as plt
        plt.show()

    print("\nDone!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate side-by-side baseline vs philosophy comparison."
    )
    parser.add_argument(
        "puzzles",
        nargs="+",
        help="Puzzle name(s) (e.g., panopticon) or 'philosophy_all' for all puzzles",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output path for PNG (default: analysis/figures/comparison_{puzzles}.png)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use embedding cache",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display plot interactively",
    )
    parser.add_argument(
        "--recompute-points",
        action="store_true",
        help="Recompute MDS projection even if cached points exist",
    )
    parser.add_argument(
        "--philosophy-only",
        action="store_true",
        help="Show only philosophy map without baseline comparison (no rescaling)",
    )
    parser.add_argument(
        "--emit-all",
        action="store_true",
        help="Emit per-puzzle, all-philosophy, and baseline comparison plots",
    )
    args = parser.parse_args()

    puzzle_names = args.puzzles
    puzzle_slug = "_".join(puzzle_names)
    if "philosophy_all" in puzzle_names:
        if len(puzzle_names) > 1:
            raise SystemExit("Use 'philosophy_all' alone to include every puzzle.")
        from src.puzzles import list_puzzle_names
        puzzle_names = list_puzzle_names()
        if not puzzle_names:
            raise SystemExit("No puzzles found for 'philosophy_all'.")
        puzzle_slug = "philosophy_all"
    cache_dir = None if args.no_cache else CACHE_DIR

    # Default output path depends on mode
    if args.output:
        output_path = args.output
    elif args.philosophy_only:
        output_path = FIGURES_DIR / f"{puzzle_slug}.png"
    else:
        output_path = FIGURES_DIR / f"comparison_{puzzle_slug}.png"

    if args.emit_all and args.philosophy_only:
        raise SystemExit("Use --emit-all without --philosophy-only.")

    if args.emit_all:
        # 1) Per-puzzle plot (philosophy-only)
        per_puzzle_output = FIGURES_DIR / f"{puzzle_slug}.png"
        _run_philosophy_only(
            puzzle_names=puzzle_names,
            puzzle_slug=puzzle_slug,
            output_path=per_puzzle_output,
            cache_dir=cache_dir,
            recompute_points=args.recompute_points,
            show=args.show,
        )

        # 2) All philosophy puzzles (philosophy-only)
        from src.puzzles import list_puzzle_names
        all_puzzles = list_puzzle_names()
        if not all_puzzles:
            raise SystemExit("No puzzles found for philosophy_all.")
        _run_philosophy_only(
            puzzle_names=all_puzzles,
            puzzle_slug="philosophy_all",
            output_path=FIGURES_DIR / "philosophy_all.png",
            cache_dir=cache_dir,
            recompute_points=args.recompute_points,
            show=args.show,
        )

        # 3) Baseline comparison vs all philosophy
        _run_comparison(
            puzzle_names=all_puzzles,
            puzzle_slug="philosophy_all",
            output_path=FIGURES_DIR / "comparison_philosophy_all.png",
            cache_dir=cache_dir,
            recompute_points=args.recompute_points,
            show=args.show,
        )
        return

    # Philosophy-only mode: skip baseline loading and rescaling
    if args.philosophy_only:
        _run_philosophy_only(
            puzzle_names=puzzle_names,
            puzzle_slug=puzzle_slug,
            output_path=output_path,
            cache_dir=cache_dir,
            recompute_points=args.recompute_points,
            show=args.show,
        )
        return

    _run_comparison(
        puzzle_names=puzzle_names,
        puzzle_slug=puzzle_slug,
        output_path=output_path,
        cache_dir=cache_dir,
        recompute_points=args.recompute_points,
        show=args.show,
    )


if __name__ == "__main__":
    main()
