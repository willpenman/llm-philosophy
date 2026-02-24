"""Generate side-by-side comparison of baseline vs philosophy maps.

Usage:
    python -m scripts.generate_comparison panopticon
    python -m scripts.generate_comparison panopticon sapir_whorf  # multiple puzzles
    python -m scripts.generate_comparison panopticon --output analysis/figures/comparison.png
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
)
from analysis.visualize import plot_comparison


ROOT = Path(__file__).resolve().parents[1]
RESPONSES_DIR = ROOT / "responses"
BASELINES_DIR = ROOT / "baselines" / "responses"
CACHE_DIR = ROOT / "analysis" / "embeddings"
FIGURES_DIR = ROOT / "analysis" / "figures"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate side-by-side baseline vs philosophy comparison."
    )
    parser.add_argument(
        "puzzles",
        nargs="+",
        help="Puzzle name(s) (e.g., panopticon)",
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
    args = parser.parse_args()

    puzzle_names = args.puzzles
    puzzle_slug = "_".join(puzzle_names)
    output_path = args.output or (FIGURES_DIR / f"comparison_{puzzle_slug}.png")
    cache_dir = None if args.no_cache else CACHE_DIR

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

    # Compare
    if baseline_mean_dist > 0:
        ratio = philosophy_mean_dist / baseline_mean_dist
        print(f"\nPhilosophy differentiation is {ratio:.2f}x baseline")

    # Generate title
    if len(puzzle_names) == 1:
        philosophy_title = f"Philosophy: {puzzle_names[0].replace('_', ' ').title()}"
    else:
        philosophy_title = f"Philosophy: {len(puzzle_names)} puzzles"

    # Generate plot
    fig = plot_comparison(
        baseline_points=baseline_points,
        philosophy_points=philosophy_points,
        baseline_title=f"Baseline Tasks ({len(baseline_by_prompt)} prompts)",
        philosophy_title=philosophy_title,
        baseline_spread=baseline_spread,
        philosophy_spread=philosophy_spread,
        output_path=output_path,
    )

    if args.show:
        import matplotlib.pyplot as plt
        plt.show()

    print("\nDone!")


if __name__ == "__main__":
    main()
