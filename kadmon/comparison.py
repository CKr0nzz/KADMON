"""Pipeline KADMON de comparaison et cartographie des déviations anatomiques."""

from time import perf_counter
from collections.abc import Hashable, Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any

import numpy as np

from dipy.tracking.distances import bundles_distances_mdf

from .barycentric import compute_barycentric_projection, displacement_statistics
from .compression import compress_binning, compress_kmeans, compress_quickbundles
from .transport import _compute_pair_sinkhorn_scale, compute_transport


CompressionResult = tuple[np.ndarray, np.ndarray]
CompressionCache = MutableMapping[tuple[Hashable, str, tuple], CompressionResult]


class IneffectiveCompressionError(RuntimeError):
    """Indiquer qu'une compression produit trop de représentants pour continuer."""


@dataclass(frozen=True)
class ComparisonConfiguration:
    """Description déclarative d'une comparaison compression × transport."""

    compression: str
    transport: str
    compression_parameters: Mapping[str, Any]
    transport_parameters: Mapping[str, Any]


def compare_configurations(
    source_streamlines: np.ndarray,
    target_streamlines: np.ndarray,
    configurations: Mapping[str, ComparisonConfiguration],
    *,
    compression_cache: CompressionCache | None = None,
    source_compression_key: Hashable | None = None,
    target_compression_key: Hashable | None = None,
    max_cost_matrix_bytes: int | None = None,
    max_representatives: int | None = None,
    max_representative_ratio: float | None = None,
) -> dict[str, dict[str, object]]:
    """Exécuter un ensemble nommé de configurations.

    Ajouter une technique consiste à ajouter une entrée à ``configurations``.
    Les dictionnaires de paramètres sont copiés afin que leur éventuel
    enrichissement interne (notamment pour Sinkhorn) ne modifie pas l'appelant.
    """
    results: dict[str, dict[str, object]] = {}
    for name, configuration in configurations.items():
        if not isinstance(configuration, ComparisonConfiguration):
            raise TypeError(
                f"La configuration {name!r} doit être une "
                "ComparisonConfiguration."
            )
        results[name] = compare_bundles(
            source_streamlines,
            target_streamlines,
            compression=configuration.compression,
            transport=configuration.transport,
            compression_parameters=dict(configuration.compression_parameters),
            transport_parameters=dict(configuration.transport_parameters),
            compression_cache=compression_cache,
            source_compression_key=source_compression_key,
            target_compression_key=target_compression_key,
            max_cost_matrix_bytes=max_cost_matrix_bytes,
            max_representatives=max_representatives,
            max_representative_ratio=max_representative_ratio,
        )
    return results


def _freeze_compression_parameters(parameters: dict[str, Any]) -> tuple:
    """Construire une clé immuable et déterministe avec tous les paramètres."""

    def freeze(value: Any) -> Hashable:
        if isinstance(value, dict):
            return tuple(sorted((key, freeze(item)) for key, item in value.items()))
        if isinstance(value, (list, tuple)):
            return tuple(freeze(item) for item in value)
        if isinstance(value, np.generic):
            return value.item()
        if not isinstance(value, Hashable):
            raise TypeError(
                f"Paramètre de compression non utilisable comme clé : {value!r}"
            )
        return value

    return tuple(sorted((key, freeze(value)) for key, value in parameters.items()))


def _compress_with_optional_cache(
    bundle: np.ndarray,
    *,
    compression: str,
    compression_parameters: dict[str, Any],
    compress,
    cache: CompressionCache | None,
    acquisition_key: Hashable | None,
) -> CompressionResult:
    """Compresser une acquisition ou réutiliser exactement le même résultat."""
    if cache is None:
        return compress(bundle, **compression_parameters)
    if acquisition_key is None:
        raise ValueError(
            "Une clé d'acquisition est requise lorsqu'un cache de compression est fourni."
        )

    cache_key = (
        acquisition_key,
        compression,
        _freeze_compression_parameters(compression_parameters),
    )
    if cache_key not in cache:
        cache[cache_key] = compress(bundle, **compression_parameters)
    return cache[cache_key]


def _compute_mdf_cost_matrix(
    source: np.ndarray,
    target: np.ndarray,
) -> np.ndarray:
    """Calculer avec DIPY la matrice MDF source-cible non normalisée."""
    if source.shape[1] != target.shape[1]:
        raise ValueError("Les représentants doivent avoir le même nombre de points.")

    return np.asarray(
        bundles_distances_mdf(source, target),
        dtype=np.float64,
    )


def _estimate_dense_memory_bytes(
    n_source: int,
    n_target: int,
    transport: str,
) -> int:
    """Estimer le pic des matrices denses MDF et OT sur CPU."""
    cross = n_source * n_target
    elements = cross
    if transport == "sinkhorn":
        elements += n_source**2 + n_target**2
        workspace_factor = 8
    else:
        workspace_factor = 4
    return elements * np.dtype(np.float64).itemsize * workspace_factor


def compare_bundles(
    source_streamlines: np.ndarray,
    target_streamlines: np.ndarray,
    *,
    compression: str,
    transport: str,
    compression_parameters: dict[str, Any],
    transport_parameters: dict[str, Any],
    compression_cache: CompressionCache | None = None,
    source_compression_key: Hashable | None = None,
    target_compression_key: Hashable | None = None,
    max_cost_matrix_bytes: int | None = None,
    max_representatives: int | None = None,
    max_representative_ratio: float | None = None,
) -> dict[str, object]:
    """Exécuter compression, MDF, OT et projection en conservant les unités mm."""
    source = np.asarray(source_streamlines, dtype=np.float64)
    target = np.asarray(target_streamlines, dtype=np.float64)
    if compression == "quickbundles":
        compress = compress_quickbundles
    elif compression == "kmeans":
        compress = compress_kmeans
    elif compression == "binning":
        compress = compress_binning
    else:
        raise ValueError(
            "La compression doit être « quickbundles », « kmeans » ou « binning »."
        )

    compression_start = perf_counter()
    source_reps, source_weights = _compress_with_optional_cache(
        source,
        compression=compression,
        compression_parameters=compression_parameters,
        compress=compress,
        cache=compression_cache,
        acquisition_key=source_compression_key,
    )
    target_reps, target_weights = _compress_with_optional_cache(
        target,
        compression=compression,
        compression_parameters=compression_parameters,
        compress=compress,
        cache=compression_cache,
        acquisition_key=target_compression_key,
    )
    compression_time = perf_counter() - compression_start

    if max_representatives is not None:
        if max_representatives <= 0:
            raise ValueError("Le nombre maximal de représentants doit être positif.")
        if max(len(source_reps), len(target_reps)) > max_representatives:
            raise IneffectiveCompressionError(
                f"Compression {compression!r} trop volumineuse : "
                f"{len(source_reps)} représentants source et "
                f"{len(target_reps)} représentants cible; "
                f"limite={max_representatives}."
            )

    if max_representative_ratio is not None:
        if not 0 < max_representative_ratio <= 1:
            raise ValueError(
                "Le ratio maximal de représentants doit appartenir à ]0, 1]."
            )
        source_ratio = len(source_reps) / len(source)
        target_ratio = len(target_reps) / len(target)
        if max(source_ratio, target_ratio) > max_representative_ratio:
            raise IneffectiveCompressionError(
                f"Compression {compression!r} insuffisante : "
                f"{len(source_reps)}/{len(source)} représentants source "
                f"({source_ratio:.1%}) et "
                f"{len(target_reps)}/{len(target)} représentants cible "
                f"({target_ratio:.1%}); limite={max_representative_ratio:.1%}."
            )

    if max_cost_matrix_bytes is not None:
        if max_cost_matrix_bytes <= 0:
            raise ValueError("La limite mémoire de la comparaison doit être positive.")
        estimated_peak_bytes = _estimate_dense_memory_bytes(
            len(source_reps), len(target_reps), transport
        )
        if estimated_peak_bytes > max_cost_matrix_bytes:
            raise MemoryError(
                "Comparaison dense trop grande : "
                f"{len(source_reps)} x {len(target_reps)} représentants, "
                f"pic estimé={estimated_peak_bytes / 2**20:.1f} Mio "
                f"(limite {max_cost_matrix_bytes / 2**20:.1f} Mio)."
            )

    mdf_start = perf_counter()
    cross_cost = _compute_mdf_cost_matrix(source_reps, target_reps)
    source_self_cost = None
    target_self_cost = None
    if transport == "sinkhorn":
        source_self_cost = _compute_mdf_cost_matrix(source_reps, source_reps)
        target_self_cost = _compute_mdf_cost_matrix(target_reps, target_reps)
        scale = _compute_pair_sinkhorn_scale(
            cross_cost, source_self_cost, target_self_cost
        )
        transport_parameters = {
            **transport_parameters,
            "source_self_cost_matrix": source_self_cost,
            "target_self_cost_matrix": target_self_cost,
            "cost_scale": scale,
        }
    mdf_time = perf_counter() - mdf_start

    transport_start = perf_counter()
    transport_result = compute_transport(
        source_weights,
        target_weights,
        cross_cost,
        transport,
        **transport_parameters,
    )
    transport_time = perf_counter() - transport_start
    plan = np.asarray(transport_result["transport_plan"], dtype=np.float64)
    transported_mass = float(plan.sum())
    if transported_mass <= 0:
        raise RuntimeError("Le plan de transport a une masse nulle.")

    projection = compute_barycentric_projection(source_reps, target_reps, plan)
    statistics = displacement_statistics(
        np.asarray(projection["representative_distance_mm"], dtype=np.float64),
        np.asarray(projection["row_mass"], dtype=np.float64),
    )
    global_distance_mm = float(np.sum(plan * cross_cost) / transported_mass)
    metrics: dict[str, object] = {
        "configuration": f"{compression}+{transport}",
        "compression": compression,
        "transport": transport,
        "source_n_representatives": len(source_reps),
        "target_n_representatives": len(target_reps),
        "source_compression_ratio": len(source_reps) / len(source),
        "target_compression_ratio": len(target_reps) / len(target),
        "compression_time_s": compression_time,
        "mdf_time_s": mdf_time,
        "transport_time_s": transport_time,
        "global_distance_mm": global_distance_mm,
        "transport_objective_normalized": transport_result["distance"],
        "transported_mass": transported_mass,
        **statistics,
    }
    return {
        "metrics": metrics,
        "source_streamlines": source,
        "target_streamlines": target,
        "source_representatives": source_reps,
        "target_representatives": target_reps,
        "source_weights": source_weights,
        "target_weights": target_weights,
        "cost_matrix_mdf_mm": cross_cost,
        "source_self_cost_matrix": source_self_cost,
        "target_self_cost_matrix": target_self_cost,
        "transport": transport_result,
        "barycentric": projection,
    }
