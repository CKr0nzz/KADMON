"""Calcul et agrégation des métriques de ré-identification."""

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd


def bundle_reid_metrics(
    bundle_name: str,
    distances: Sequence[float],
    *,
    comparison_subjects: Sequence[str],
    intra_identity_subject: str,
    mean_displacement_mm: float,
    mean_transported_mass: float,
    mean_n_representatives: float,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Résumer le classement du vrai retest parmi les sujets candidats."""
    distances = np.asarray(distances, dtype=np.float64)
    subjects = tuple(comparison_subjects)
    if distances.shape != (len(subjects),):
        raise ValueError(
            f"{len(subjects)} distances attendues, forme reçue={distances.shape}."
        )
    if not np.isfinite(distances).all():
        raise ValueError("Les distances RE-ID doivent toutes être finies.")

    try:
        intra_index = subjects.index(intra_identity_subject)
    except ValueError as exc:
        raise ValueError("Le sujet intra-identité est absent des candidats.") from exc

    intra_distance = float(distances[intra_index])
    inter_distances = np.delete(distances, intra_index)
    mean_inter_distance = float(inter_distances.mean())
    if mean_inter_distance <= 0:
        raise ValueError(
            f"Distance moyenne inter-identité invalide : {mean_inter_distance}"
        )

    order = np.argsort(distances, kind="stable")
    metrics = {
        "bundle": bundle_name,
        "intra_inter_ratio": intra_distance / mean_inter_distance,
        "intra_identity_top1_success": bool(np.argmin(distances) == intra_index),
        "intra_identity_rank": int(np.flatnonzero(order == intra_index)[0] + 1),
        "intra_inter_separation_margin_mm": float(
            inter_distances.min() - intra_distance
        ),
        "intra_identity_distance_mm": intra_distance,
        "mean_inter_identity_distance_mm": mean_inter_distance,
        "mean_displacement_mm": float(mean_displacement_mm),
        "mean_transported_mass": float(mean_transported_mass),
        "mean_n_representatives": float(mean_n_representatives),
    }
    if extra:
        metrics.update(extra)
    return metrics


def aggregate_reid_metrics(
    bundle_metrics: pd.DataFrame,
    *,
    n_comparison_subjects: int,
    elapsed_s: float,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Agréger les résultats de tous les bundles d'un essai Optuna."""
    if bundle_metrics.empty:
        raise ValueError("Aucune métrique de bundle à agréger.")
    valid = bundle_metrics["intra_identity_top1_success"].astype(bool)
    aggregates = {
        "reid_valid_bundles": bundle_metrics.loc[valid, "bundle"].tolist(),
        "reid_failed_bundles": bundle_metrics.loc[~valid, "bundle"].tolist(),
        "mean_intra_inter_ratio": float(bundle_metrics["intra_inter_ratio"].mean()),
        "median_intra_inter_ratio": float(
            bundle_metrics["intra_inter_ratio"].median()
        ),
        "intra_identity_top1_accuracy": float(valid.mean()),
        "mean_intra_identity_rank": float(
            bundle_metrics["intra_identity_rank"].mean()
        ),
        "mean_intra_inter_separation_margin_mm": float(
            bundle_metrics["intra_inter_separation_margin_mm"].mean()
        ),
        "mean_intra_identity_distance_mm": float(
            bundle_metrics["intra_identity_distance_mm"].mean()
        ),
        "mean_inter_identity_distance_mm": float(
            bundle_metrics["mean_inter_identity_distance_mm"].mean()
        ),
        "mean_displacement_mm": float(bundle_metrics["mean_displacement_mm"].mean()),
        "mean_transported_mass": float(
            bundle_metrics["mean_transported_mass"].mean()
        ),
        "mean_n_representatives": float(
            bundle_metrics["mean_n_representatives"].mean()
        ),
        "n_bundles": int(len(bundle_metrics)),
        "n_comparisons": int(len(bundle_metrics) * n_comparison_subjects),
        "elapsed_s": float(elapsed_s),
    }
    if extra:
        aggregates.update(extra)
    return aggregates


def set_trial_metrics(trial: Any, metrics: Mapping[str, Any]) -> None:
    """Attacher des métriques sérialisables à un essai Optuna."""
    for name, value in metrics.items():
        if isinstance(value, np.generic):
            value = value.item()
        trial.set_user_attr(name, value)
