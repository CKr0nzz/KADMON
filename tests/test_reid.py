import numpy as np
import pandas as pd
from types import SimpleNamespace

from kadmon.protocol import HCP_REID_PROTOCOL, ReidProtocol
from kadmon.reid import aggregate_reid_metrics, bundle_reid_metrics
from kadmon.selection import select_best_reid_trial


def test_hcp_protocol_derives_subject_groups():
    protocol = HCP_REID_PROTOCOL
    assert protocol.reference_subject == "103818"
    assert protocol.intra_identity_subject == "103818_re"
    assert protocol.subjects[0] == protocol.reference_subject
    assert len(protocol.comparison_subjects) == 10


def test_protocol_copies_subject_mapping():
    pairs = {"source": "source_re"}
    protocol = ReidProtocol(pairs, "source")
    pairs["other"] = "other_re"
    assert protocol.subjects == ("source", "source_re")


def test_bundle_and_aggregate_reid_metrics():
    first = bundle_reid_metrics(
        "bundle-a",
        [1.0, 4.0, 2.0],
        comparison_subjects=("same", "other-a", "other-b"),
        intra_identity_subject="same",
        mean_displacement_mm=2.5,
        mean_transported_mass=0.8,
        mean_n_representatives=20,
    )
    second = {**first, "bundle": "bundle-b", "intra_identity_top1_success": False}
    aggregated = aggregate_reid_metrics(
        pd.DataFrame([first, second]),
        n_comparison_subjects=3,
        elapsed_s=1.25,
    )

    assert np.isclose(first["intra_inter_ratio"], 1 / 3)
    assert first["intra_identity_rank"] == 1
    assert first["intra_inter_separation_margin_mm"] == 1.0
    assert aggregated["reid_valid_bundles"] == ["bundle-a"]
    assert aggregated["reid_failed_bundles"] == ["bundle-b"]
    assert aggregated["intra_identity_top1_accuracy"] == 0.5
    assert aggregated["n_comparisons"] == 6


def test_reid_selection_prioritizes_top1_over_raw_ratio():
    def trial(number, value, top1):
        return SimpleNamespace(
            number=number,
            value=value,
            state=SimpleNamespace(name="COMPLETE"),
            user_attrs={
                "intra_identity_top1_accuracy": top1,
                "mean_intra_identity_rank": 1.0,
                "mean_intra_inter_ratio": value,
                "mean_transported_mass": 0.8,
            },
        )

    raw_ratio_best = trial(0, 0.2, 0.8)
    reid_best = trial(1, 0.3, 0.9)
    assert select_best_reid_trial([raw_ratio_best, reid_best]) is reid_best
