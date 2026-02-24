"""Distance computation and dimensionality reduction.

Computes pairwise cosine distances between model embeddings
and projects to 2D using metric MDS.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from sklearn.manifold import MDS
from sklearn.metrics.pairwise import cosine_distances


@dataclass
class ModelPoint:
    """A model's position in 2D space."""
    provider: str
    model: str
    x: float
    y: float


def compute_distance_matrix(
    embeddings: dict[tuple[str, str], np.ndarray],
) -> tuple[np.ndarray, list[tuple[str, str]]]:
    """Compute pairwise cosine distance matrix.

    Args:
        embeddings: Dict mapping (provider, model) to embedding

    Returns:
        Tuple of (distance matrix, ordered list of (provider, model) keys)
    """
    keys = list(embeddings.keys())
    n = len(keys)

    if n == 0:
        return np.zeros((0, 0)), []

    # Stack embeddings into matrix
    matrix = np.stack([embeddings[k] for k in keys])

    # Compute cosine distances
    distances = cosine_distances(matrix)

    return distances, keys


def project_to_2d(
    distance_matrix: np.ndarray,
    keys: list[tuple[str, str]],
    random_state: int = 42,
) -> list[ModelPoint]:
    """Project distance matrix to 2D using metric MDS.

    Args:
        distance_matrix: Pairwise distance matrix
        keys: Ordered list of (provider, model) tuples
        random_state: Random seed for reproducibility

    Returns:
        List of ModelPoint objects with 2D coordinates
    """
    n = len(keys)

    if n == 0:
        return []

    if n == 1:
        # Single point at origin
        return [ModelPoint(
            provider=keys[0][0],
            model=keys[0][1],
            x=0.0,
            y=0.0,
        )]

    if n == 2:
        # Two points on a line, separated by their distance
        d = distance_matrix[0, 1]
        return [
            ModelPoint(provider=keys[0][0], model=keys[0][1], x=-d/2, y=0.0),
            ModelPoint(provider=keys[1][0], model=keys[1][1], x=d/2, y=0.0),
        ]

    # Use metric MDS for 3+ points
    # metric="precomputed" means we pass a distance matrix directly
    # metric_mds=True means use metric (vs non-metric) MDS
    mds = MDS(
        n_components=2,
        metric="precomputed",
        metric_mds=True,
        n_init=4,
        init="random",
        random_state=random_state,
        normalized_stress="auto",
    )

    coords = mds.fit_transform(distance_matrix)

    return [
        ModelPoint(
            provider=keys[i][0],
            model=keys[i][1],
            x=float(coords[i, 0]),
            y=float(coords[i, 1]),
        )
        for i in range(n)
    ]


def compute_spread(points: list[ModelPoint]) -> float:
    """Compute the spread (variance) of points.

    Useful for comparing baseline vs philosophy spreads.
    """
    if len(points) < 2:
        return 0.0

    xs = [p.x for p in points]
    ys = [p.y for p in points]

    var_x = np.var(xs)
    var_y = np.var(ys)

    return float(var_x + var_y)


def compute_mean_pairwise_distance(distance_matrix: np.ndarray) -> float:
    """Compute mean pairwise distance (excluding diagonal)."""
    n = distance_matrix.shape[0]
    if n < 2:
        return 0.0

    # Get upper triangle (excluding diagonal)
    upper = distance_matrix[np.triu_indices(n, k=1)]
    return float(np.mean(upper))


def compute_averaged_distance_matrix(
    per_task_embeddings: dict[str, dict[tuple[str, str], np.ndarray]],
) -> tuple[np.ndarray, list[tuple[str, str]]]:
    """Compute distance matrix by averaging pairwise distances across tasks.

    For each model pair, computes cosine distance on each task where both
    models have embeddings, then averages those distances.

    Args:
        per_task_embeddings: Dict mapping task_name to {(provider, model): embedding}

    Returns:
        Tuple of (averaged distance matrix, ordered list of (provider, model) keys)
    """
    # Find models that appear in at least one task
    all_models: set[tuple[str, str]] = set()
    for task_embeddings in per_task_embeddings.values():
        all_models.update(task_embeddings.keys())

    keys = sorted(all_models)
    n = len(keys)

    if n == 0:
        return np.zeros((0, 0)), []

    # For each model pair, accumulate distances across tasks
    distance_sums = np.zeros((n, n))
    distance_counts = np.zeros((n, n))

    for task_name, task_embeddings in per_task_embeddings.items():
        # Get models present in this task
        task_keys = [k for k in keys if k in task_embeddings]
        if len(task_keys) < 2:
            continue

        # Build embedding matrix for this task
        task_matrix = np.stack([task_embeddings[k] for k in task_keys])
        task_distances = cosine_distances(task_matrix)

        # Map back to full matrix indices
        task_indices = [keys.index(k) for k in task_keys]

        for ti, i in enumerate(task_indices):
            for tj, j in enumerate(task_indices):
                if i != j:
                    distance_sums[i, j] += task_distances[ti, tj]
                    distance_counts[i, j] += 1

    # Compute averages (avoid division by zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        avg_distances = np.divide(distance_sums, distance_counts)
        avg_distances = np.nan_to_num(avg_distances, nan=0.0)

    # Ensure diagonal is zero
    np.fill_diagonal(avg_distances, 0.0)

    return avg_distances, keys
