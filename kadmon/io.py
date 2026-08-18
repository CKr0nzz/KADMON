"""Chargement et mise en cache des bundles."""

from pathlib import Path

import numpy as np
from dipy.io.streamline import load_trk
from dipy.tracking.streamline import set_number_of_points


def load_bundle(path: Path, n_points=12) -> np.ndarray:
    """Charger un bundle ``.trk`` ou un cache ``.npy``."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Bundle introuvable : {path}")
    if n_points < 2:
        raise ValueError("n_points doit être supérieur ou égal à 2.")

    if path.suffix.lower() == ".npy":
        return np.load(path)
    if path.suffix.lower() != ".trk":
        raise ValueError("Format non pris en charge; utilisez un fichier .trk ou .npy.")

    streamlines = load_trk(
        str(path),
        "same",
        bbox_valid_check=False,
    ).streamlines
    if len(streamlines) == 0:
        raise ValueError("Le bundle ne contient aucune streamline.")

    return np.asarray(
        set_number_of_points(streamlines, n_points),
        dtype=np.float64,
    )

