"""Generate side-by-side comparison of baseline vs philosophy maps.

Usage:
    python -m scripts.generate_comparison panopticon
    python -m scripts.generate_comparison panopticon --output analysis/figures/comparison.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from analysis.embeddings import embed_all_responses, embed_all_baseline_responses
from analysis.distances import (
    compute_distance_matrix,
    project_to_2d,
    compute_spread,
    compute_mean_pairwise_distance,
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
    parser.add_argument("puzzle", help="Puzzle name (e.g., panopticon)")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output path for PNG (default: analysis/figures/comparison_{puzzle}.png)",
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

    puzzle_name = args.puzzle
    output_path = args.output or (FIGURES_DIR / f"comparison_{puzzle_name}.png")
    cache_dir = None if args.no_cache else CACHE_DIR

    # Load baseline embeddings
    print("Loading baseline responses...")
    baseline_embeddings = embed_all_baseline_responses(
        baselines_dir=BASELINES_DIR,
        cache_dir=cache_dir,
    )

    if not baseline_embeddings:
        print("No baseline responses found. Run `python -m scripts.run_baselines --model ALL` first.")
        return

    print(f"Found {len(baseline_embeddings)} models with baselines")

    # Load philosophy embeddings
    print(f"\nLoading philosophy responses for '{puzzle_name}'...")
    philosophy_embeddings = embed_all_responses(
        responses_dir=RESPONSES_DIR,
        puzzle_name=puzzle_name,
        cache_dir=cache_dir,
    )

    if not philosophy_embeddings:
        print(f"No philosophy responses found for puzzle '{puzzle_name}'")
        return

    print(f"Found {len(philosophy_embeddings)} models with philosophy responses")

    # Find common models
    common_models = set(baseline_embeddings.keys()) & set(philosophy_embeddings.keys())
    print(f"\n{len(common_models)} models have both baseline and philosophy responses")

    if len(common_models) < 2:
        print("Need at least 2 common models for comparison. Run more baselines.")
        return

    # Filter to common models
    baseline_filtered = {k: v for k, v in baseline_embeddings.items() if k in common_models}
    philosophy_filtered = {k: v for k, v in philosophy_embeddings.items() if k in common_models}

    # Compute distances for baselines
    baseline_distances, baseline_keys = compute_distance_matrix(baseline_filtered)
    baseline_mean_dist = compute_mean_pairwise_distance(baseline_distances)
    baseline_points = project_to_2d(baseline_distances, baseline_keys)
    baseline_spread = compute_spread(baseline_points)

    print(f"\nBaseline: mean distance = {baseline_mean_dist:.4f}, spread = {baseline_spread:.4f}")

    # Compute distances for philosophy
    philosophy_distances, philosophy_keys = compute_distance_matrix(philosophy_filtered)
    philosophy_mean_dist = compute_mean_pairwise_distance(philosophy_distances)
    philosophy_points = project_to_2d(philosophy_distances, philosophy_keys)
    philosophy_spread = compute_spread(philosophy_points)

    print(f"Philosophy: mean distance = {philosophy_mean_dist:.4f}, spread = {philosophy_spread:.4f}")

    # Compare
    if baseline_mean_dist > 0:
        ratio = philosophy_mean_dist / baseline_mean_dist
        print(f"\nPhilosophy differentiation is {ratio:.2f}x baseline")

    # Generate plot
    fig = plot_comparison(
        baseline_points=baseline_points,
        philosophy_points=philosophy_points,
        baseline_title="Baseline Tasks",
        philosophy_title=f"Philosophy: {puzzle_name.replace('_', ' ').title()}",
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
