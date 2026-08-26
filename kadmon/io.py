"""Découverte, chargement et mise en cache des bundles."""

from pathlib import Path
from typing import Iterable

import numpy as np
from dipy.io.streamline import load_trk
from dipy.tracking.streamline import set_number_of_points


class BundleCollection:
    """Bundles ``.npy`` communs à plusieurs sujets d'une étude.

    Les tableaux sont chargés à la demande avec un memory map et conservés dans
    ``cache``. L'index ``files`` reste public pour les caches de compression qui
    ont besoin des métadonnées du fichier source.
    """

    def __init__(
        self,
        root: Path,
        subjects: Iterable[str],
        *,
        n_points: int = 12,
        selected: Iterable[str] | None = None,
        subdirectory: str = "nn_8mm",
    ) -> None:
        if n_points < 2:
            raise ValueError("n_points doit être supérieur ou égal à 2.")

        self.root = Path(root)
        self.subjects = tuple(subjects)
        if not self.subjects:
            raise ValueError("Au moins un sujet est requis.")
        self.n_points = n_points
        self.cache: dict[tuple[str, str], np.ndarray] = {}

        suffix = f"_{n_points}mpts_rasmm.npy"
        self.files = {
            subject: {
                path.name[: -len(suffix)]: path
                for path in sorted(
                    (self.root / subject / subdirectory).glob(f"*{suffix}")
                )
            }
            for subject in self.subjects
        }
        common_names = set.intersection(*(set(index) for index in self.files.values()))

        if selected is not None:
            selected = tuple(selected)
            missing = sorted(set(selected) - common_names)
            if missing:
                raise ValueError(f"Bundles demandés absents : {missing}")
            selected_names = set(selected)
            common_names &= selected_names

        self.names = sorted(common_names)
        if not self.names:
            raise RuntimeError(
                "Aucun bundle commun au protocole de ré-identification."
            )

    def load(self, subject: str, bundle_name: str) -> np.ndarray:
        """Charger et valider un bundle, puis le conserver en cache."""
        key = (subject, bundle_name)
        if key not in self.cache:
            try:
                path = self.files[subject][bundle_name]
            except KeyError as exc:
                raise KeyError(f"Bundle inconnu : {subject}/{bundle_name}") from exc

            bundle = np.load(path, mmap_mode="r")
            if (
                bundle.ndim != 3
                or bundle.shape[1:] != (self.n_points, 3)
                or len(bundle) == 0
                or not np.isfinite(bundle).all()
            ):
                raise ValueError(
                    f"Bundle invalide : {subject}/{bundle_name}, "
                    f"forme={bundle.shape}"
                )
            self.cache[key] = bundle
        return self.cache[key]

    def clear(self) -> None:
        """Libérer les références vers les tableaux chargés."""
        self.cache.clear()


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
