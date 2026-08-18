"""Backend CUDA partagé pour MDF et Sinkhorn débiaisé.

Ce module contient uniquement les primitives numériques communes aux études
Optuna. La compression et l'orchestration des essais restent dans les
notebooks, puisqu'elles diffèrent entre K-Means et le binning.
"""

from __future__ import annotations

import gc
from collections.abc import MutableMapping
from typing import Any

import numpy as np
import torch
from dipy.tracking.distances import bundles_distances_mdf

from .barycentric import compute_barycentric_projection, displacement_statistics
from .transport import _compute_pair_sinkhorn_scale, compute_transport


GpuSelfCostCache = MutableMapping[int, tuple[torch.Tensor, torch.Tensor]]


def compute_mdf_cost_matrix_gpu(
    source: torch.Tensor,
    target: torch.Tensor,
    *,
    batch_size: int,
) -> torch.Tensor:
    """Calculer la matrice MDF orientée par blocs sur CUDA."""
    if source.device.type != "cuda" or target.device.type != "cuda":
        raise RuntimeError("Tenseurs CUDA requis.")
    if batch_size < 1:
        raise ValueError("batch_size doit être positif.")
    if source.ndim != 3 or target.ndim != 3 or source.shape[1:] != target.shape[1:]:
        raise ValueError("Les représentants GPU doivent avoir la forme (N, P, 3).")

    result = torch.empty(
        (len(source), len(target)), dtype=source.dtype, device=source.device
    )
    target_reverse = target.flip(1)
    for start in range(0, len(source), int(batch_size)):
        block = source[start : start + int(batch_size)]
        direct = torch.linalg.vector_norm(
            block[:, None] - target[None], dim=-1
        ).mean(-1)
        reverse = torch.linalg.vector_norm(
            block[:, None] - target_reverse[None], dim=-1
        ).mean(-1)
        result[start : start + len(block)] = torch.minimum(direct, reverse)
    if not bool(torch.isfinite(result).all()):
        raise FloatingPointError("Coût MDF GPU invalide.")
    return result


def positive_p95_gpu(
    *matrices: torch.Tensor,
    max_samples_per_matrix: int = 1_000_000,
) -> torch.Tensor:
    """Estimer de façon déterministe le P95 positif sans pic mémoire GPU."""
    if not matrices:
        raise ValueError("Au moins une matrice est requise.")
    if max_samples_per_matrix < 1:
        raise ValueError("max_samples_per_matrix doit être positif.")

    samples = []
    for matrix in matrices:
        flat = matrix.detach().reshape(-1)
        step = max(
            1,
            (flat.numel() + max_samples_per_matrix - 1)
            // max_samples_per_matrix,
        )
        values = flat[::step]
        values = values[values > 0]
        if values.numel():
            samples.append(values.cpu())
    if not samples:
        first = matrices[0]
        return torch.ones((), dtype=first.dtype, device=first.device)
    return torch.quantile(torch.cat(samples), 0.95).to(
        device=matrices[0].device, dtype=matrices[0].dtype
    )


def _sinkhorn_cost_gpu(
    source_weights: torch.Tensor,
    target_weights: torch.Tensor,
    cost: torch.Tensor,
    parameters: dict[str, Any],
    *,
    return_plan: bool,
) -> tuple[torch.Tensor, torch.Tensor | None]:
    """Résoudre un coût Sinkhorn logarithmique avec contrôle de convergence."""
    import ot

    solver = ot.sinkhorn if return_plan else ot.sinkhorn2
    value, log = solver(
        source_weights,
        target_weights,
        cost,
        reg=float(parameters["epsilon"]),
        method="sinkhorn_log",
        numItermax=int(parameters["max_iter"]),
        stopThr=float(parameters["stop_threshold"]),
        log=True,
    )
    errors = log.get("err", [])
    last_error = errors[-1] if errors else np.inf
    final_error = (
        float(last_error.detach().cpu())
        if torch.is_tensor(last_error)
        else float(last_error)
    )
    if not np.isfinite(final_error) or final_error > parameters["reject_threshold"]:
        raise RuntimeError(f"Sinkhorn GPU non convergé: {final_error:.3e}")
    if return_plan:
        return torch.sum(value * cost), value
    return value, None


def compute_sinkhorn_gpu(
    source_weights: np.ndarray,
    target_weights: np.ndarray,
    cross_cost: torch.Tensor,
    source_self_cost: torch.Tensor,
    target_self_cost: torch.Tensor,
    parameters: dict[str, Any],
) -> tuple[torch.Tensor, torch.Tensor]:
    """Calculer divergence Sinkhorn débiaisée et plan croisé sur CUDA."""
    device, dtype = cross_cost.device, cross_cost.dtype
    source = torch.as_tensor(source_weights, dtype=dtype, device=device)
    target = torch.as_tensor(target_weights, dtype=dtype, device=device)
    source = source / source.sum()
    target = target / target.sum()
    scale = positive_p95_gpu(cross_cost, source_self_cost, target_self_cost)

    # Les auto-coûts ne produisent pas de plan; les résoudre d'abord limite le
    # nombre de grands tableaux vivants lorsque le plan croisé est construit.
    source_value, _ = _sinkhorn_cost_gpu(
        source, source, source_self_cost / scale, parameters, return_plan=False
    )
    target_value, _ = _sinkhorn_cost_gpu(
        target, target, target_self_cost / scale, parameters, return_plan=False
    )
    cross_value, plan = _sinkhorn_cost_gpu(
        source, target, cross_cost / scale, parameters, return_plan=True
    )
    assert plan is not None
    divergence = torch.clamp(
        cross_value - 0.5 * source_value - 0.5 * target_value, min=0
    )
    return divergence, plan


def _check_gpu_memory(
    n_source: int,
    n_target: int,
    *,
    dtype: torch.dtype,
    device: torch.device,
    memory_fraction: float | None,
) -> None:
    if memory_fraction is None:
        return
    if not 0 < memory_fraction <= 1:
        raise ValueError("memory_fraction doit appartenir à ]0, 1].")
    free_bytes, _ = torch.cuda.mem_get_info(device)
    largest = max(n_source * n_source, n_target * n_target, n_source * n_target)
    matrices = n_source**2 + n_target**2 + n_source * n_target
    estimated_peak = torch.empty((), dtype=dtype).element_size() * (
        12 * largest + matrices
    )
    if estimated_peak > memory_fraction * free_bytes:
        raise MemoryError(
            "Comparaison GPU refusée avant allocation: "
            f"pic estimé={estimated_peak / 2**30:.2f} Gio, "
            f"libre={free_bytes / 2**30:.2f} Gio"
        )


def evaluate_pair_gpu(
    source_distribution: tuple[np.ndarray, np.ndarray],
    target_distribution: tuple[np.ndarray, np.ndarray],
    parameters: dict[str, Any],
    *,
    device: torch.device,
    dtype: torch.dtype = torch.float32,
    batch_size: int = 128,
    memory_fraction: float | None = None,
    self_cost_cache: GpuSelfCostCache | None = None,
    return_cost: bool = False,
    log: bool = False,
) -> dict[str, object]:
    """Évaluer une paire compressée avec MDF et Sinkhorn sur CUDA."""
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("CUDA est requis pour evaluate_pair_gpu().")
    source_reps, source_weights = source_distribution
    target_reps, target_weights = target_distribution
    _check_gpu_memory(
        len(source_reps), len(target_reps), dtype=dtype, device=device,
        memory_fraction=memory_fraction,
    )

    cache = self_cost_cache

    def tensor_and_self_cost(representatives: np.ndarray):
        key = id(representatives)
        if cache is not None and key in cache:
            return cache[key]
        tensor = torch.as_tensor(representatives, dtype=dtype, device=device)
        self_cost = compute_mdf_cost_matrix_gpu(
            tensor, tensor, batch_size=batch_size
        )
        if cache is not None:
            cache[key] = (tensor, self_cost)
        return tensor, self_cost

    source, source_self = tensor_and_self_cost(source_reps)
    target, target_self = tensor_and_self_cost(target_reps)
    cross = compute_mdf_cost_matrix_gpu(source, target, batch_size=batch_size)
    objective, plan_gpu = compute_sinkhorn_gpu(
        source_weights, target_weights, cross, source_self, target_self, parameters
    )
    if log:
        print(
            f"[GPU] Cost matrix: shape={tuple(cross.shape)}, dtype={cross.dtype}\n"
            "[GPU] OT backend: PyTorch/POT"
        )

    global_distance_mm = float(
        (torch.sum(plan_gpu * cross) / torch.sum(plan_gpu)).detach().cpu()
    )
    plan = plan_gpu.detach().cpu().numpy().astype(np.float64)
    cost = (
        cross.detach().cpu().numpy().astype(np.float64) if return_cost else None
    )
    projection = compute_barycentric_projection(source_reps, target_reps, plan)
    statistics = displacement_statistics(
        np.asarray(projection["representative_distance_mm"]),
        np.asarray(projection["row_mass"]),
    )
    result = {
        "cost": cost,
        "weights": (source_weights, target_weights),
        "objective": float(objective.detach().cpu()),
        "global_distance_mm": global_distance_mm,
        "mean_mm": float(statistics["mean_mm"]),
        "mass": float(plan.sum()),
    }
    if cache is None:
        del source, target, source_self, target_self
    del cross, plan_gpu, plan, projection, objective
    return result


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
    """Référence CPU commune servant aussi de fallback et de validation."""
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


def release_gpu_memory() -> None:
    """Déclencher le GC Python et libérer le cache d'allocation CUDA."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
