"""Sélection cohérente des essais Optuna de ré-identification."""

from collections.abc import Iterable
from typing import Any


def reid_selection_key(trial: Any) -> tuple[float, float, float, float]:
    """Ordonner un essai par Top-1, rang, ratio, puis couverture.

    La clé est destinée à ``min`` : le Top-1 et la masse transportée sont donc
    inversés, tandis que le rang et le ratio sont minimisés directement.
    """
    attributes = trial.user_attrs
    required = (
        "intra_identity_top1_accuracy",
        "mean_intra_identity_rank",
        "mean_intra_inter_ratio",
        "mean_transported_mass",
    )
    missing = [name for name in required if name not in attributes]
    if missing:
        raise ValueError(
            f"L'essai {getattr(trial, 'number', '?')} ne contient pas : {missing}."
        )
    return (
        -float(attributes["intra_identity_top1_accuracy"]),
        float(attributes["mean_intra_identity_rank"]),
        float(attributes["mean_intra_inter_ratio"]),
        -float(attributes["mean_transported_mass"]),
    )


def select_best_reid_trial(trials: Iterable[Any]) -> Any:
    """Sélectionner le meilleur essai COMPLETE selon la règle RE-ID commune."""
    completed = [
        trial
        for trial in trials
        if getattr(getattr(trial, "state", None), "name", None) == "COMPLETE"
        and trial.value is not None
    ]
    if not completed:
        raise ValueError("Aucun essai Optuna COMPLETE n'est disponible.")
    return min(completed, key=reid_selection_key)
