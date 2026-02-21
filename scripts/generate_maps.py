"""Generate 2D model similarity maps.

Usage:
    python -m scripts.generate_maps panopticon
    python -m scripts.generate_maps panopticon --output analysis/figures/panopticon.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from analysis.embeddings import embed_all_responses
from analysis.distances import (
    compute_distance_matrix,
    project_to_2d,
    compute_spread,
    compute_mean_pairwise_distance,
)
from analysis.visualize import plot_model_map


ROOT = Path(__file__).resolve().parents[1]
RESPONSES_DIR = ROOT / "responses"
CACHE_DIR = ROOT / "analysis" / "embeddings"
FIGURES_DIR = ROOT / "analysis" / "figures"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 2D model similarity map for a puzzle."
    )
    parser.add_argument("puzzle", help="Puzzle name (e.g., panopticon)")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output path for PNG (default: analysis/figures/{puzzle}.png)",
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
    output_path = args.output or (FIGURES_DIR / f"{puzzle_name}.png")
    cache_dir = None if args.no_cache else CACHE_DIR

    print(f"Loading responses for puzzle '{puzzle_name}'...")
    embeddings = embed_all_responses(
        responses_dir=RESPONSES_DIR,
        puzzle_name=puzzle_name,
        cache_dir=cache_dir,
    )

    if not embeddings:
        print(f"No responses found for puzzle '{puzzle_name}'")
        return

    print(f"Found {len(embeddings)} model responses")

    # Compute distances
    distance_matrix, keys = compute_distance_matrix(embeddings)
    mean_dist = compute_mean_pairwise_distance(distance_matrix)
    print(f"Mean pairwise cosine distance: {mean_dist:.4f}")

    # Project to 2D
    points = project_to_2d(distance_matrix, keys)
    spread = compute_spread(points)
    print(f"2D spread (variance): {spread:.4f}")

    # Plot
    title = f"Model Similarity: {puzzle_name.replace('_', ' ').title()}"
    subtitle = f"Mean cosine distance: {mean_dist:.4f}"

    fig = plot_model_map(
        points=points,
        title=title,
        subtitle=subtitle,
        output_path=output_path,
    )

    if args.show:
        import matplotlib.pyplot as plt
        plt.show()

    print("Done!")


if __name__ == "__main__":
    main()
