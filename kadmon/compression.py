"""Compression de bundles par QuickBundles, K-Means ou binning."""

import numpy as np
from dipy.segment.clustering import QuickBundles

from sklearn.neighbors import KDTree
from tractosearch.binning import simplify


def compress_quickbundles(
    bundle: np.ndarray,
    *,
    threshold: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Compresser un bundle avec QuickBundles et pondérer ses centroïdes."""
    if threshold <= 0:
        raise ValueError("Le seuil QuickBundles doit être strictement positif.")

    clusters = QuickBundles(threshold=threshold).cluster(bundle)
    representatives = np.asarray(clusters.centroids, dtype=np.float64)
    counts = np.asarray(
        [len(cluster.indices) for cluster in clusters],
        dtype=np.float64,
    )
    if not len(representatives) or counts.sum() <= 0:
        raise RuntimeError("QuickBundles n'a produit aucun représentant pondérable.")

    return representatives, counts / counts.sum()


def _assign_to_centroids(
    bundle: np.ndarray,
    centroids: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Assigner chaque streamline au centroïde le plus proche."""
    tree = KDTree(centroids.reshape(len(centroids), -1))

    direct_streamlines = bundle.reshape(len(bundle), -1)
    reversed_streamlines = bundle[:, ::-1].reshape(len(bundle), -1)

    direct_distances, direct_centroid_ids = tree.query(direct_streamlines, k=1)
    reversed_distances, reversed_centroid_ids = tree.query(reversed_streamlines, k=1)

    direct_distances = direct_distances[:, 0]
    reversed_distances = reversed_distances[:, 0]

    direct_centroid_ids = direct_centroid_ids[:, 0]
    reversed_centroid_ids = reversed_centroid_ids[:, 0]

    should_reverse = reversed_distances < direct_distances

    assigned_centroid_ids = np.where(
        should_reverse,
        reversed_centroid_ids,
        direct_centroid_ids,
    )

    oriented_bundle = bundle.copy()
    oriented_bundle[should_reverse] = oriented_bundle[should_reverse, ::-1]

    return assigned_centroid_ids, oriented_bundle


def compress_kmeans(
    bundle: np.ndarray,
    *,
    n_clusters: int,
    max_iter: int = 300,
    tol: float = 1e-4,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Compresser un bundle par K-Means orienté et retourner les centroïdes avec leurs poids."""
    n_streamlines = len(bundle)

    if not 1 <= n_clusters <= n_streamlines:
        raise ValueError(f"Le nombre de clusters doit être entre 1 et {n_streamlines}.")

    if max_iter <= 0 or tol <= 0:
        raise ValueError("max_iter et tol doivent être strictement positifs.")

    rng = np.random.default_rng(seed)
    initial_indices = rng.choice(n_streamlines, size=n_clusters, replace=False)
    centroids = bundle[initial_indices].copy()

    for _ in range(max_iter):
        previous_centroids = centroids.copy()
        assigned_centroid_ids, oriented_bundle = _assign_to_centroids(bundle, centroids)

        # Ancienne version avec une boucle Python sur chaque cluster :
        # for centroid_id in range(n_clusters):
        #     member_indices = np.flatnonzero(
        #         assigned_centroid_ids == centroid_id
        #     )
        #
        #     if member_indices.size > 0:
        #         centroids[centroid_id] = oriented_bundle[
        #             member_indices
        #         ].mean(axis=0)
        #     else:
        #         random_index = rng.integers(n_streamlines)
        #         centroids[centroid_id] = bundle[random_index]

        cluster_counts = np.bincount(assigned_centroid_ids, minlength=n_clusters)
        centroid_sums = np.zeros_like(centroids)
        np.add.at(centroid_sums, assigned_centroid_ids, oriented_bundle)


        # Masks
        non_empty_clusters = cluster_counts > 0
        empty_clusters = cluster_counts == 0

        # NumPy compare les dimensions en partant de la droite
        centroids[non_empty_clusters] = (
            centroid_sums[non_empty_clusters]
            / cluster_counts[non_empty_clusters, np.newaxis, np.newaxis]
        )

        n_empty_clusters = np.count_nonzero(empty_clusters)
        if n_empty_clusters:
            random_indices = rng.integers(n_streamlines, size=n_empty_clusters)
            centroids[empty_clusters] = bundle[random_indices]

        centroid_shift = np.linalg.norm(centroids - previous_centroids)

        if centroid_shift < tol:
            break

    assigned_centroid_ids, _ = _assign_to_centroids(bundle, centroids)

    cluster_counts = np.bincount(assigned_centroid_ids, minlength=n_clusters)

    non_empty_clusters = cluster_counts > 0
    representatives = centroids[non_empty_clusters]

    representative_counts = cluster_counts[non_empty_clusters].astype(np.float64)

    weights = representative_counts / representative_counts.sum()

    return representatives, weights


def compress_binning(
    streamlines: np.ndarray,
    *,
    bin_size: float,
    binning_nb: int,
    method: str,
    n_points: int = 12,
) -> tuple[np.ndarray, np.ndarray]:
    """Compresser un bundle en représentants pondérés par binning."""
    if bin_size <= 0:
        raise ValueError("La taille des bins doit être strictement positive.")
    if binning_nb not in (2, 3):
        raise ValueError("Le nombre de mean-points de binning doit être 2 ou 3.")
    if method not in ("mean", "median"):
        raise ValueError("La méthode de binning doit être 'mean' ou 'median'.")
    if n_points < 2:
        raise ValueError("n_points doit être supérieur ou égal à 2.")

    representatives, counts = simplify(
        streamlines,
        bin_size=bin_size,
        binning_nb=binning_nb,
        method=method,
        nb_mpts=n_points,
        return_count=True,
        dtype=np.float64,
    )

    representatives = np.asarray(representatives, dtype=np.float64)

    weights = counts / counts.sum()

    return representatives, weights
