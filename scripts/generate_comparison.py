"""Generate model similarity visualizations.

Usage:
    # Side-by-side comparison of baseline vs philosophy responses
    python -m scripts.generate_comparison panopticon
    python -m scripts.generate_comparison panopticon sapir_whorf  # multiple puzzles

    # Philosophy-only mode (no baseline comparison, no rescaling)
    python -m scripts.generate_comparison panopticon --philosophy-only
    python -m scripts.generate_comparison panopticon sapir_whorf --philosophy-only

    # When adding a model, 'recompute' both the philosophy-only and the comparison (they use separate cached points)
    python -m scripts.generate_comparison philosophy_all --philosophy-only --recompute-points
    python -m scripts.generate_comparison philosophy_all --recompute-points

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
    # Check for cached points
    philosophy_points_cache = CACHE_DIR / f"points_philosophy_only_{puzzle_slug}.json"

    if not recompute_points:
        philosophy_points = load_points(philosophy_points_cache)

        if philosophy_points is not None:
            print("Using cached points (use --recompute-points to regenerate)")
            spread = compute_spread(philosophy_points)
            mean_dist = compute_mean_pairwise_distance_points(philosophy_points)

            title = _display_title(puzzle_slug)
            subtitle = f"Mean distance: {mean_dist:.4f}, Spread: {spread:.4f}"

            fig = plot_model_map(
                points=philosophy_points,
                title=title,
                subtitle=subtitle,
                output_path=output_path,
            )

            if show:
                import matplotlib.pyplot as plt
                plt.show()

            print("\nDone!")
            return

    # Load baseline model list (to filter to common models)
    print("Loading baseline responses (for model filtering)...")
    baseline_by_prompt = embed_baseline_responses_by_prompt(
        baselines_dir=BASELINES_DIR,
        cache_dir=cache_dir,
    )

    baseline_models: set[tuple[str, str]] = set()
    for prompt_embeddings in baseline_by_prompt.values():
        baseline_models.update(prompt_embeddings.keys())

    # Load philosophy embeddings
    print(f"Loading philosophy responses for {puzzle_names}...")
    philosophy_by_puzzle = embed_puzzle_responses_by_puzzle(
        responses_dir=RESPONSES_DIR,
        puzzle_names=puzzle_names,
        cache_dir=cache_dir,
    )

    if not philosophy_by_puzzle:
        print(f"No philosophy responses found for puzzles: {puzzle_names}")
        return

    # Count models across puzzles
    philosophy_models: set[tuple[str, str]] = set()
    for puzzle_embeddings in philosophy_by_puzzle.values():
        philosophy_models.update(puzzle_embeddings.keys())

    print(f"Found {len(philosophy_models)} models across {len(philosophy_by_puzzle)} puzzles")

    # Filter to common models (same as comparison mode)
    common_models = baseline_models & philosophy_models
    print(f"{len(common_models)} models have both baseline and philosophy responses")

    if len(common_models) < 2:
        print("Need at least 2 common models for visualization.")
        return

    philosophy_filtered = {
        puzzle: {k: v for k, v in emb.items() if k in common_models}
        for puzzle, emb in philosophy_by_puzzle.items()
    }

    # Compute averaged distances (no rescaling needed)
    philosophy_distances, philosophy_keys = compute_averaged_distance_matrix(philosophy_filtered)
    mean_dist = compute_mean_pairwise_distance(philosophy_distances)
    philosophy_points = project_to_2d(philosophy_distances, philosophy_keys)
    spread = compute_spread(philosophy_points)

    print(f"Mean cosine distance: {mean_dist:.4f}, Spread: {spread:.4f}")

    # Cache computed points
    save_points(philosophy_points, philosophy_points_cache)
    print(f"Cached points to {philosophy_points_cache}")

    # Generate plot
    title = _display_title(puzzle_slug)
    subtitle = f"Mean distance: {mean_dist:.4f}, Spread: {spread:.4f}"

    fig = plot_model_map(
        points=philosophy_points,
        title=title,
        subtitle=subtitle,
        output_path=output_path,
    )

    if show:
        import matplotlib.pyplot as plt
        plt.show()

    print("\nDone!")


def _run_comparison(
    puzzle_names: list[str],
    puzzle_slug: str,
    output_path: Path,
    cache_dir: Path | None,
    recompute_points: bool,
    show: bool,
) -> None:
    """Generate baseline vs philosophy comparison plot."""
    # Check for cached points (comparison mode)
    baseline_points_cache = CACHE_DIR / "points_baseline.json"
    philosophy_points_cache = CACHE_DIR / f"points_{puzzle_slug}.json"

    if not recompute_points:
        baseline_points = load_points(baseline_points_cache)
        philosophy_points = load_points(philosophy_points_cache)

        if baseline_points is not None and philosophy_points is not None:
            print("Using cached points (use --recompute-points to regenerate)")

            philosophy_title = (
                "Philosophy Positions (All Puzzles)"
                if puzzle_slug == "philosophy_all"
                else "Philosophy Positions"
            )

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
            return

    # Load baseline embeddings (per-prompt)
    print("Loading baseline responses (per-prompt)...")
    baseline_by_prompt = embed_baseline_responses_by_prompt(
        baselines_dir=BASELINES_DIR,
        cache_dir=cache_dir,
    )

    if not baseline_by_prompt:
        print("No baseline responses found. Run `python -m scripts.run_baselines --model ALL` first.")
        return

    # Count models across prompts
    baseline_models: set[tuple[str, str]] = set()
    for prompt_embeddings in baseline_by_prompt.values():
        baseline_models.update(prompt_embeddings.keys())

    print(f"Found {len(baseline_models)} models across {len(baseline_by_prompt)} baseline prompts")

    # Load philosophy embeddings (per-puzzle)
    print(f"\nLoading philosophy responses for {puzzle_names}...")
    philosophy_by_puzzle = embed_puzzle_responses_by_puzzle(
        responses_dir=RESPONSES_DIR,
        puzzle_names=puzzle_names,
        cache_dir=cache_dir,
    )

    if not philosophy_by_puzzle:
        print(f"No philosophy responses found for puzzles: {puzzle_names}")
        return

    # Count models across puzzles
    philosophy_models: set[tuple[str, str]] = set()
    for puzzle_embeddings in philosophy_by_puzzle.values():
        philosophy_models.update(puzzle_embeddings.keys())

    print(f"Found {len(philosophy_models)} models across {len(philosophy_by_puzzle)} puzzles")

    # Find common models
    # NOTE: We filter to the intersection of baseline and philosophy responses. This
    # discards models that have philosophy responses but no baseline (or vice versa).
    # This is a conservative choice: we have more data than we use here, but averaging
    # distances across incomplete pairings is not well-defined mathematically. A model
    # missing from one prompt/puzzle would leave gaps in the distance matrix, and it's
    # unclear how to weight partial comparisons. For now, we accept this limitation.
    common_models = baseline_models & philosophy_models
    print(f"\n{len(common_models)} models have both baseline and philosophy responses")

    if len(common_models) < 2:
        print("Need at least 2 common models for comparison. Run more baselines.")
        return

    # Filter to common models
    baseline_filtered = {
        prompt: {k: v for k, v in emb.items() if k in common_models}
        for prompt, emb in baseline_by_prompt.items()
    }
    philosophy_filtered = {
        puzzle: {k: v for k, v in emb.items() if k in common_models}
        for puzzle, emb in philosophy_by_puzzle.items()
    }

    # Compute averaged distances for baselines
    baseline_distances, baseline_keys = compute_averaged_distance_matrix(baseline_filtered)
    baseline_mean_dist = compute_mean_pairwise_distance(baseline_distances)
    baseline_points = project_to_2d(baseline_distances, baseline_keys)
    baseline_points_mean = compute_mean_pairwise_distance_points(baseline_points)
    baseline_scale = (baseline_mean_dist / baseline_points_mean) if baseline_points_mean > 0 else 1.0
    baseline_points = scale_points(baseline_points, baseline_scale)
    baseline_spread = compute_spread(baseline_points)

    print(
        f"\nBaseline: mean distance = {baseline_mean_dist:.4f}, "
        f"scale factor = {baseline_scale:.4f}, spread = {baseline_spread:.4f}"
    )

    # Compute averaged distances for philosophy
    philosophy_distances, philosophy_keys = compute_averaged_distance_matrix(philosophy_filtered)
    philosophy_mean_dist = compute_mean_pairwise_distance(philosophy_distances)
    philosophy_points = project_to_2d(philosophy_distances, philosophy_keys)
    philosophy_points_mean = compute_mean_pairwise_distance_points(philosophy_points)
    philosophy_scale = (philosophy_mean_dist / philosophy_points_mean) if philosophy_points_mean > 0 else 1.0
    philosophy_points = scale_points(philosophy_points, philosophy_scale)
    philosophy_spread = compute_spread(philosophy_points)

    print(
        f"Philosophy: mean distance = {philosophy_mean_dist:.4f}, "
        f"scale factor = {philosophy_scale:.4f}, spread = {philosophy_spread:.4f}"
    )

    # Cache computed points
    save_points(baseline_points, baseline_points_cache)
    save_points(philosophy_points, philosophy_points_cache)
    print(f"\nCached points to {baseline_points_cache} and {philosophy_points_cache}")

    # Compare
    if baseline_mean_dist > 0:
        ratio = philosophy_mean_dist / baseline_mean_dist
        print(f"\nPhilosophy differentiation is {ratio:.2f}x baseline")

    philosophy_title = (
        "Philosophy Positions (All Puzzles)"
        if puzzle_slug == "philosophy_all"
        else "Philosophy Positions"
    )

    # Generate plot (use default titles)
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
