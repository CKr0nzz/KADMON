"""Projection barycentrique orientée et déplacements géométriques en RASMM."""

import numpy as np
from numpy.typing import NDArray


def _orient_targets_per_source(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Orienter chaque représentant cible relativement à chaque représentant source."""
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    if source.shape[1:] != target.shape[1:]:
        raise ValueError("Les streamlines sources et cibles sont incompatibles.")
    oriented = np.empty(
        (
            len(source),
            len(target),
            *source.shape[1:],
        ),
        dtype=np.float64,
    )
    for source_index, source_streamline in enumerate(source):
        direct = np.linalg.norm(
            target - source_streamline,
            axis=2,
        ).mean(axis=1)

        reverse = np.linalg.norm(
            target[:, ::-1] - source_streamline,
            axis=2,
        ).mean(axis=1)

        oriented[source_index] = target
        flip = reverse < direct
        oriented[source_index, flip] = target[flip, ::-1]

    return oriented


def _compute_projection(
    plan: NDArray[np.float64],
    oriented: NDArray[np.float64],
    row_mass: NDArray[np.float64],
    valid: NDArray[np.bool_],
) -> NDArray[np.float64]:
    """Calculer la moyenne barycentrique des représentants cibles orientés."""
    projection = np.full(
        oriented.shape[:1] + oriented.shape[2:],
        np.nan,
        dtype=np.float64,
    )
    for source_index in np.flatnonzero(valid):
        #j = cible (target)
        #p = point de la streamline
        #c = coordonnée (x, y, z)
        # "j,jpc->pc" multiplie chaque cible j par son poids, somme sur j,
        # puis conserve les axes point et coordonnée.
        projection[source_index] = (
            np.einsum(
                "j,jpc->pc",
                plan[source_index],
                oriented[source_index],
            )
            / row_mass[source_index]
        )
    return projection


def _compute_displacements(
    source: NDArray[np.float64],
    projection: NDArray[np.float64],
    valid: NDArray[np.bool_],
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Calculer les déplacements des représentants sources en mm."""
    vectors = projection - source
    point_magnitude = np.linalg.norm(vectors, axis=2)
    representative_distance = np.full(len(source), np.nan, dtype=np.float64)
    representative_distance[valid] = point_magnitude[valid].mean(axis=1)
    return vectors, point_magnitude, representative_distance


def compute_barycentric_projection(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
    transport_plan: NDArray[np.float64],
    *,
    mass_tolerance: float = 1e-12,
) -> dict[str, object]:
    """Projeter les représentants sources et mesurer leurs déplacements en mm."""
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    plan = np.asarray(transport_plan, dtype=np.float64)
    if plan.shape != (
        len(source),
        len(target),
    ):
        raise ValueError("Le plan est incompatible avec les streamlines.")
    if not np.isfinite(plan).all() or np.any(plan < 0):
        raise ValueError("Le plan de transport est invalide.")

    # Masse totale du plan OT
    row_mass = plan.sum(axis=1)

    valid = row_mass > mass_tolerance
    oriented = _orient_targets_per_source(source, target)
    projection = _compute_projection(plan, oriented, row_mass, valid)
    displacement_vectors, point_displacement_mm, representative_distance_mm = (
        _compute_displacements(source, projection, valid)
    )

    return {
        "projection": projection,
        "displacement_vectors": displacement_vectors,
        "point_displacement_mm": point_displacement_mm,
        "representative_distance_mm": representative_distance_mm,
        "row_mass": row_mass,
        "valid_mask": valid,
    }


def displacement_statistics(
    representative_distance_mm: NDArray[np.float64],
    row_mass: NDArray[np.float64],
) -> dict[str, float | int]:
    """Calculer les statistiques pondérées des représentants sources valides."""
    distances = np.asarray(
        representative_distance_mm,
        dtype=np.float64,
    )
    mass = np.asarray(row_mass, dtype=np.float64)
    valid = np.isfinite(distances) & np.isfinite(mass) & (mass > 0)
    if not np.any(valid):
        raise ValueError("Aucune streamline source n'a reçu de masse.")
    values = distances[valid]
    weights = mass[valid] / mass[valid].sum()
    order = np.argsort(values)
    sorted_values = values[order]
    # Permet de savoir quand on a atteint 95%
    cumulative = np.cumsum(weights[order])

    def weighted_percentile(quantile: float) -> float:
        index = np.searchsorted(cumulative, quantile, side="left")
        return float(sorted_values[index])

    return {
        "mean_mm": float(np.sum(values * weights)),
        "median_mm": weighted_percentile(0.5),
        "max_mm": float(values.max()),
        "p95_mm": weighted_percentile(0.95),
        "n_valid_representatives": int(valid.sum()),
        "n_untransported_representatives": int((~valid).sum()),
    }
