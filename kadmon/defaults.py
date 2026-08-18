"""Paramètres scientifiques par défaut de KADMON."""

# Profil anatomique QuickBundles + Partial OT, trial 75.
QUICKBUNDLES_PARTIAL_THRESHOLD = 7.0
QUICKBUNDLES_PARTIAL_MASS = 0.99

# Profil anatomique QuickBundles + Sinkhorn, trial 114.
QUICKBUNDLES_SINKHORN_THRESHOLD = 6.0
QUICKBUNDLES_SINKHORN_EPSILON = 0.08744817112699642

KMEANS_PARTIAL_K = 40
KMEANS_PARTIAL_MASS = 0.63

# Compromis anatomique Binning + Partial OT, trial Optuna 55.
BINNING_PARTIAL_BIN_SIZE = 16.0
BINNING_PARTIAL_BINNING_NB = 2
BINNING_PARTIAL_REPRESENTATIVE = "mean"
BINNING_PARTIAL_MASS = 0.68

# Compromis anatomique/LDDMM K-Means + Sinkhorn, trial Optuna 130.
KMEANS_SINKHORN_K = 155
KMEANS_SINKHORN_EPSILON = 0.017736980940270066

# Optimum Binning + Sinkhorn du trial Optuna 374. Cette configuration conserve
# la résolution anatomique la plus fine parmi les compromis retenus.
BINNING_SINKHORN_BIN_SIZE = 8.0
BINNING_SINKHORN_BINNING_NB = 2
BINNING_SINKHORN_REPRESENTATIVE = "mean"
BINNING_SINKHORN_EPSILON = 0.025172673855518923
