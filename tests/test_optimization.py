from pathlib import Path

import optuna

from kadmon.optimization import (
    StudyRunPolicy,
    count_complete_trials,
    create_reid_study,
    run_until_complete,
)


def test_run_until_target_complete_trials(tmp_path: Path):
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = create_reid_study(tmp_path / "study.sqlite3", "test", seed=42)

    def objective(trial):
        return trial.suggest_float("value", 0.0, 1.0)

    completed = run_until_complete(
        study,
        objective,
        StudyRunPolicy(target_complete_trials=3, trials_per_batch=1),
    )
    assert completed == 3
    assert count_complete_trials(study) == 3
