# KADMON

**Kantorovich Anatomical Deviation Mapping of Neurotracts**

## Overview

KADMON is a Python research project for comparing homologous white-matter
bundles from any two tractography datasets. Source and target acquisitions are
selected independently, so the same workflow supports comparisons between
subjects, sessions, retests, or reconstruction outputs.

The name refers to the Kantorovich formulation of optimal transport used to
estimate correspondences and map local anatomical deviations between
neurotracts. Its Python API is exposed directly through `kadmon`.

Inputs may be TrackVis (`.trk`) files or preprocessed NumPy (`.npy`) caches. All bundles are
expected to use a common RASMM coordinate space.

## Main features

- Single-pair and batch bundle comparisons
- Streamline resampling and bundle compression with QuickBundles, K-Means, or
  TractoSearch binning
- MDF-based geometric costs and optimal-transport comparisons
- Distances and displacement statistics reported in millimetres
- Optional transport-plan, projection, and 3D figure exports

## Repository structure

```text
KADMON/
├── kadmon/        Reusable Python modules, including the shared CUDA backend
├── notebooks/     Interactive analyses, Optuna studies, and bundle data
│   ├── bundles/   Tractography data organized by subject
│   └── optuna/    Six compression × transport optimization notebooks
└── README.md
```

Each acquisition is stored in its own subdirectory under `notebooks/bundles/`.
KADMON does not interpret subject names or automatically add suffixes such
as `_re`. Generated results should be written to a separate output directory.

## Installation

KADMON requires Python 3.10 or newer. Create an isolated environment and
install the third-party dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy scipy scikit-learn dipy POT tractosearch lpqtree
python -m pip install pandas jupyterlab joblib optuna plotly
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

TractoSearch is required for bundle binning. When working from a local
TractoSearch checkout, install it in editable mode instead:

```bash
python -m pip install -e /path/to/TractoSearch
```

Install the optional visualization stack with:

```bash
python -m pip install fury vtk
```

PyTorch is required by the Sinkhorn Optuna notebooks, including for their CPU
fallback. The command above installs its CPU build. To enable the shared CUDA
backend, install instead a PyTorch build compatible with the local NVIDIA
driver. Each Sinkhorn notebook validates its GPU results against the CPU
implementation before using CUDA and falls back explicitly to CPU if validation
or CUDA availability fails.

The repository itself is not installed as a Python package.

## Quick start

### Notebook

Launch JupyterLab from the repository root:

```bash
jupyter lab
```

Open `notebooks/1_Comparer_Techniques_OT.ipynb` to compare all six techniques
on one bundle pair. Then use `notebooks/2_Visualiser_Deplacements_3D.ipynb`
for the local FURY visualization of the selected technique. Set the two bundle
paths and run the cells in order:

```python
from pathlib import Path

SOURCE_PATH = Path(
    "notebooks/bundles/103818/nn_8mm/tractosearch_nn_8_0mm_all_CC_1_m.trk"
)
TARGET_PATH = Path(
    "notebooks/bundles/433839/nn_8mm/tractosearch_nn_8_0mm_all_CC_1_m.trk"
)
```

The notebook validates and loads these files directly. Paths are relative to
the directory from which JupyterLab was started.

The default compression and optimal transport parameters were selected through
an Optuna hyperparameter optimization performed during the research phase.
They are intended as reasonable starting values and may need to be retuned for
datasets with different characteristics.

The executable defaults prioritize anatomical coverage and representation
resolution while retaining strong RE-ID. QuickBundles + Partial OT uses trial
75 (`threshold=7 mm`, `mass=0.99`, Top-1 `93.55%`, about 296
representatives). QuickBundles + Sinkhorn uses trial 114 (`threshold=6 mm`,
`epsilon=0.08744817112699642`, Top-1 `90.32%`, about 538 representatives).
The notebooks also report the separate best-RE-ID selection based on Top-1,
mean identity rank, intra/inter ratio, and transported mass.

The default K-Means + Partial OT configuration uses the higher-coverage trial
44: `n_clusters=40` and `mass=0.63`. K-Means + Sinkhorn uses the
LDDMM-oriented trial 130: `n_clusters=155` and
`epsilon=0.017736980940270066`. Binning + Partial OT uses the higher-coverage
trial 55: `bin_size=16`, `binning_nb=2`, `representative=mean`, and
`mass=0.68`.
Binning + Sinkhorn uses the anatomy-preserving optimum from Optuna trial 374:
`bin_size=8`, `binning_nb=2`, `representative=mean`, and
`epsilon=0.025172673855518923`. These values can be changed directly in the
notebook configuration cells when testing another dataset.

## Optuna studies

The six studies use the same 31-bundle RE-ID protocol and store their trials in
`notebooks/optuna/studies/optuna_reid.sqlite3`:

```text
00_quickbundles_partial_optuna.ipynb
01_quickbundles_sinkhorn_optuna.ipynb
02_kmeans_partial_optuna.ipynb
03_kmeans_sinkhorn_optuna.ipynb
04_binning_partial_optuna.ipynb
05_binning_sinkhorn_optuna.ipynb
```

QuickBundles and K-Means compression use up to eight CPU workers. Sinkhorn
trials run sequentially and use the shared PyTorch/POT CUDA backend for MDF,
self-costs, cross-costs, and entropic transport when GPU validation succeeds.

## Core dependencies

- **NumPy** — streamline arrays and numerical operations
- **SciPy** — sparse numerical operations
- **DIPY** — tractography I/O, resampling, and MDF distances
- **DIPY QuickBundles** — tractography-specific compression baseline
- **POT** — optimal-transport solvers
- **PyTorch** — Sinkhorn backend, with optional CUDA acceleration
- **scikit-learn** — KDTree-based operations
- **TractoSearch** (required) and **lpqtree** — streamline binning utilities
- **FURY** and **VTK** — optional 3D visualization
- **Optuna** and **Plotly** — hyperparameter studies and study visualizations
- **pandas**, **Joblib**, and **JupyterLab** — tables, CPU parallelism, and notebooks

## Future work

A possible research direction is to use the Sinkhorn transport plan to
initialize LDDMM-based bundle registration. Its soft correspondences between
streamline representatives could provide a meaningful starting point for
deformable registration. Combining Sinkhorn with LDDMM may also help assess
whether the inferred deformations are anatomically plausible, providing a
richer characterization of bundle differences than transport distances alone.
This direction has not yet been evaluated or implemented in KADMON.

## Acknowledgements

This project was developed as part of a research internship at the Université
du Québec en Outaouais (UQO).

The author would like to thank Étienne St-Onge for his supervision, guidance
and valuable discussions throughout the project.
