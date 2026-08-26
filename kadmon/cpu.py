"""Référence CPU pour les comparaisons MDF et Sinkhorn débiaisées."""

from typing import Any

import numpy as np
from dipy.tracking.distances import bundles_distances_mdf

from .barycentric import compute_barycentric_projection, displacement_statistics
from .transport import _compute_pair_sinkhorn_scale, compute_transport


def available_ram_bytes() -> int:
    """Retourner la mémoire RAM disponible sous Linux, ou zéro."""
    try:
        with open("/proc/meminfo", encoding="utf-8") as stream:
            fields = {
                line.split(":", 1)[0]: int(line.split()[1]) * 1024
                for line in stream
                if ":" in line
            }
        return fields.get("MemAvailable", 0)
    except OSError:
        return 0


def evaluate_pair_cpu(
    source_distribution: tuple[np.ndarray, np.ndarray],
    target_distribution: tuple[np.ndarray, np.ndarray],
    parameters: dict[str, Any],
    *,
    memory_fraction: float | None = None,
) -> dict[str, object]:
    """Évaluer une paire sur CPU pour le fallback et la validation du GPU."""
    source_reps, source_weights = source_distribution
    target_reps, target_weights = target_distribution
    if memory_fraction is not None:
        if not 0 < memory_fraction <= 1:
            raise ValueError("memory_fraction doit appartenir à ]0, 1].")
        matrix_elements = (
            len(source_reps) ** 2
            + len(target_reps) ** 2
            + len(source_reps) * len(target_reps)
        )
        required = 8 * np.dtype(np.float64).itemsize * matrix_elements
        available = available_ram_bytes()
        if available and required > memory_fraction * available:
            raise MemoryError(
                "Comparaison CPU refusée: "
                f"pic estimé={required / 2**30:.2f} Gio, "
                f"disponible={available / 2**30:.2f} Gio"
            )

    cross = np.asarray(
        bundles_distances_mdf(source_reps, target_reps), dtype=np.float64
    )
    source_self = np.asarray(
        bundles_distances_mdf(source_reps, source_reps), dtype=np.float64
    )
    target_self = np.asarray(
        bundles_distances_mdf(target_reps, target_reps), dtype=np.float64
    )
    scale = _compute_pair_sinkhorn_scale(cross, source_self, target_self)
    transport = compute_transport(
        source_weights,
        target_weights,
        cross,
        "sinkhorn",
        **parameters,
        source_self_cost_matrix=source_self,
        target_self_cost_matrix=target_self,
        cost_scale=scale,
    )
    plan = np.asarray(transport["transport_plan"])
    projection = compute_barycentric_projection(source_reps, target_reps, plan)
    statistics = displacement_statistics(
        np.asarray(projection["representative_distance_mm"]),
        np.asarray(projection["row_mass"]),
    )
    mass = float(plan.sum())
    return {
        "cost": cross,
        "weights": (source_weights, target_weights),
        "objective": float(transport["distance"]),
        "global_distance_mm": float(np.sum(plan * cross) / mass),
        "mean_mm": float(statistics["mean_mm"]),
        "mass": mass,
    }
