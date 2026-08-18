"""Transport optimal de Kantorovich pour les correspondances KADMON."""

from typing import Any

import numpy as np
import ot
from numpy.typing import NDArray


def _normalize_weights(
    weights: np.ndarray,
    expected_size: int,
) -> NDArray[np.float64]:
    result = np.asarray(weights, dtype=np.float64)
    if result.shape != (expected_size,):
        raise ValueError("Le nombre de poids ne correspond pas à la matrice de coût.")

    return result / result.sum()


def _normalize_partial_cost(cost_matrix: np.ndarray):
    """Normaliser la matrice de coût dans [0, 1] pour le calcul du Partial OT."""
    cost = np.asarray(cost_matrix, dtype=np.float64)
    maximum = float(cost.max())

    if maximum > 0:
        cost = cost / maximum

    return cost


def _compute_partial(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
    cost: NDArray[np.float64],
    *,
    mass: float = 0.0,
    nb_dummies: int = 100,
) -> dict[str, object]:
    """Calculer un plan de transport optimal partiel."""
    if not 0.0 < mass <= 1.0:
        raise ValueError("La masse Partial OT doit appartenir à ]0, 1].")
    if nb_dummies <= 0:
        raise ValueError("Le nombre de points réservoirs doit être positif.")

    normalized_cost = _normalize_partial_cost(cost)

    # Plusieurs dummies stabilisent le solveur Partial OT et évitent ses erreurs.
    plan = np.asarray(
        ot.partial.partial_wasserstein(
            source,
            target,
            normalized_cost,
            m=mass,
            nb_dummies=nb_dummies,
        ),
        dtype=np.float64,
    )
    distance = float(np.sum(plan * normalized_cost))

    return {
        "distance": distance,
        "transport_plan": plan,
    }


def _compute_pair_sinkhorn_scale(
    cross_cost: np.ndarray,
    source_self_cost: np.ndarray,
    target_self_cost: np.ndarray,
    *,
    percentile: float = 95.0,
) -> float:
    """Calculer l'échelle Sinkhorn à partir des distances positives."""
    positive_distances = []

    for matrix in (cross_cost, source_self_cost, target_self_cost):
        distances = matrix[matrix > 0]
        if distances.size:
            positive_distances.append(distances)

    if not positive_distances:
        return 1.0

    return float(np.percentile(np.concatenate(positive_distances), percentile))


def _sinkhorn_cost(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
    normalized_cost: NDArray[np.float64],
    *,
    epsilon: float,
    max_iter: int,
    stop_threshold: float,
    reject_threshold: float,
    return_plan: bool,
) -> tuple[float, NDArray[np.float64] | None, dict[str, float | int]]:
    """Exécuter Sinkhorn logarithmique.

    Si ``return_plan`` est True, retourne le plan de transport optimal.
    Sinon, retourne uniquement son coût.
    """
    solver = ot.sinkhorn if return_plan else ot.sinkhorn2
    value_or_plan, log = solver(
        source,
        target,
        normalized_cost,
        reg=epsilon,
        method="sinkhorn_log",
        numItermax=max_iter,
        stopThr=stop_threshold,
        log=True,
    )
    errors = np.asarray(log.get("err", []), dtype=np.float64)
    final_error = float(errors[-1]) if errors.size else np.inf
    n_iterations = int(log.get("niter", max_iter))
    if not np.isfinite(final_error) or final_error > reject_threshold:
        raise RuntimeError(
            "Sinkhorn non convergé : "
            f"erreur finale={final_error:.3e}, seuil={reject_threshold:.3e}."
        )
    if return_plan:
        plan = np.asarray(value_or_plan, dtype=np.float64)
        value = float(np.sum(plan * normalized_cost))
    else:
        plan = None
        value = float(np.asarray(value_or_plan))
    if not np.isfinite(value):
        raise RuntimeError("Le coût Sinkhorn est invalide.")
    return value, plan, {
        "final_error": final_error,
        "iterations": n_iterations,
    }


def _compute_sinkhorn(
    source: NDArray[np.float64],
    target: NDArray[np.float64],
    cost: NDArray[np.float64],
    **parameters: Any,
) -> dict[str, object]:
    """Calculer plan croisé et divergence de Sinkhorn débiaisée."""
    source_self = np.asarray(parameters.get("source_self_cost_matrix"), dtype=np.float64)
    target_self = np.asarray(parameters.get("target_self_cost_matrix"), dtype=np.float64)

    if source_self.shape != (len(source), len(source)):
        raise ValueError("L'auto-coût source Sinkhorn a une forme invalide.")
    if target_self.shape != (len(target), len(target)):
        raise ValueError("L'auto-coût cible Sinkhorn a une forme invalide.")

    scale = float(parameters.get("cost_scale", 0.0))
    epsilon = float(parameters.get("epsilon", 0.0))
    max_iter = int(parameters.get("max_iter", 2000))
    stop_threshold = float(parameters.get("stop_threshold", 1e-6))
    reject_threshold = float(parameters.get("reject_threshold", 1e-5))
    if scale <= 0 or epsilon <= 0:
        raise ValueError("L'échelle et epsilon Sinkhorn doivent être positifs.")

    common = {
        "epsilon": epsilon,
        "max_iter": max_iter,
        "stop_threshold": stop_threshold,
        "reject_threshold": reject_threshold,
    }
    normalized_cost = cost / scale
    normalized_source_self = source_self / scale
    normalized_target_self = target_self / scale

    cross, plan, cross_diagnostics = _sinkhorn_cost(
        source, target, normalized_cost, return_plan=True, **common
    )
    source_auto, _, source_diagnostics = _sinkhorn_cost(
        source,
        source,
        normalized_source_self,
        return_plan=False,
        **common,
    )
    target_auto, _, target_diagnostics = _sinkhorn_cost(
        target,
        target,
        normalized_target_self,
        return_plan=False,
        **common,
    )

    # Divergence de Sinkhorn :
    # coût croisé - 1/2 coût source-source - 1/2 coût cible-cible.
    divergence = max(cross - 0.5 * source_auto - 0.5 * target_auto, 0.0)

    return {
        "distance": divergence,
        "transport_plan": plan,
        "diagnostics": {
            "cross": cross_diagnostics,
            "source_self": source_diagnostics,
            "target_self": target_diagnostics,
        },
    }


def compute_transport(
    source_weights: np.ndarray,
    target_weights: np.ndarray,
    cost_matrix: np.ndarray,
    method: str,
    **parameters: Any,
) -> dict[str, object]:
    """Calculer le transport optimal avec Partial OT ou Sinkhorn."""
    cost = np.asarray(cost_matrix, dtype=np.float64)
    if cost.ndim != 2:
        raise ValueError("La matrice de coût doit être bidimensionnelle.")
    source = _normalize_weights(source_weights, cost.shape[0])
    target = _normalize_weights(target_weights, cost.shape[1])

    if method == "partial":
        return _compute_partial(source, target, cost, **parameters)

    if method == "sinkhorn":
        return _compute_sinkhorn(source, target, cost, **parameters)

    raise ValueError("Le transport doit être « partial » ou « sinkhorn ».")
