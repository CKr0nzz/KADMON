"""Utilitaires communs pour les studies Optuna de KADMON."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
import warnings

import optuna
from optuna.trial import TrialState


@dataclass(frozen=True)
class StudyRunPolicy:
    """Politique d'exécution jusqu'à un nombre cible d'essais réussis."""

    target_complete_trials: int
    trials_per_batch: int | None = None
    max_attempt_factor: int = 4
    gc_after_trial: bool = True

    def __post_init__(self) -> None:
        if self.target_complete_trials <= 0:
            raise ValueError("target_complete_trials doit être positif.")
        if self.trials_per_batch is not None and self.trials_per_batch <= 0:
            raise ValueError("trials_per_batch doit être positif ou None.")
        if self.max_attempt_factor <= 0:
            raise ValueError("max_attempt_factor doit être positif.")


def create_reid_study(path: Path, name: str, *, seed: int) -> optuna.Study:
    """Créer ou rouvrir une study RE-ID minimisant le ratio intra/inter."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return optuna.create_study(
        study_name=name,
        storage=f"sqlite:///{path}",
        load_if_exists=True,
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )


def count_complete_trials(study: optuna.Study) -> int:
    return sum(trial.state == TrialState.COMPLETE for trial in study.trials)


def fail_stale_running_trials(study: optuna.Study) -> int:
    """Marquer les RUNNING orphelins comme échoués.

    L'appelant doit garantir qu'aucun autre worker n'utilise cette study.
    """
    running = [trial for trial in study.trials if trial.state == TrialState.RUNNING]
    for trial in running:
        study.tell(trial.number, state=TrialState.FAIL)
    return len(running)


def run_until_complete(
    study: optuna.Study,
    objective: Callable,
    policy: StudyRunPolicy,
    *,
    callbacks: Sequence[Callable] = (),
) -> int:
    """Exécuter des essais jusqu'à la cible COMPLETE ou la limite de tentatives."""
    completed = count_complete_trials(study)
    remaining = max(0, policy.target_complete_trials - completed)
    max_attempts = max(50, policy.max_attempt_factor * remaining) if remaining else 0
    attempts = 0
    print(
        f"Étude : {completed}/{policy.target_complete_trials} essais COMPLETE; "
        f"cible restante={remaining}."
    )

    while completed < policy.target_complete_trials and attempts < max_attempts:
        remaining = policy.target_complete_trials - completed
        batch_size = min(
            remaining if policy.trials_per_batch is None else policy.trials_per_batch,
            max_attempts - attempts,
        )
        study.optimize(
            objective,
            n_trials=batch_size,
            n_jobs=1,
            show_progress_bar=batch_size > 1,
            gc_after_trial=policy.gc_after_trial,
            callbacks=list(callbacks),
        )
        attempts += batch_size
        completed = count_complete_trials(study)
        print(
            f"Progression : {completed}/{policy.target_complete_trials} essais "
            f"COMPLETE après {attempts} nouvelle(s) tentative(s)."
        )

    if completed < policy.target_complete_trials:
        warnings.warn(
            f"Cible non atteinte : {completed}/{policy.target_complete_trials} "
            f"essais COMPLETE après {attempts} tentatives; relancer pour continuer.",
            RuntimeWarning,
        )
    return completed
