"""Generate small artificial counts; no embedded research observations."""
from pathlib import Path
import numpy as np
from .checks import require
from .h5ad import axis_digest
from .replay import replay, sha256, write_json
from .decomposition import decompose
from .operator import trace_operator, compare_effects
from .association import residual_rank_association
from .evidence import migrate_ids, external_catalog, validate_evidence


def write_synthetic_h5ad(path, matrix, genes, encoding="dense"):
    import h5py
    x = np.asarray(matrix)
    with h5py.File(path, "x") as f:
        f.attrs.update({"encoding-type": "anndata", "encoding-version": "0.1.0"})
        for name in ("obs", "var"):
            group = f.create_group(name)
            group.attrs.update({"encoding-type": "dataframe", "encoding-version": "0.2.0", "_index": "_index"})
        string_type = h5py.string_dtype("utf-8")
        def strings(group, name, values):
            node = group.create_dataset(name, data=np.asarray(values, dtype=object), dtype=string_type, track_times=False)
            node.attrs.update({"encoding-type": "string-array", "encoding-version": "0.2.0"})
        strings(f["var"], "_index", genes)
        strings(f["obs"], "_index", [f"SYN_CELL_{i:04d}" for i in range(len(x))])
        strings(f["obs"], "target_gene", ["non-targeting"] * len(x))
        strings(f["obs"], "ntc_id", [f"SYN_GUIDE_{i // 2:03d}" for i in range(len(x))])
        f["obs"].attrs["column-order"] = np.asarray(["target_gene", "ntc_id"], dtype=object)
        f["var"].attrs["column-order"] = np.asarray([], dtype=string_type)
        if encoding == "dense":
            node = f.create_dataset("X", data=x, track_times=False)
            node.attrs.update({"encoding-type": "array", "encoding-version": "0.2.0"})
        else:
            require(encoding == "csr_matrix", "unknown synthetic encoding")
            node = f.create_group("X")
            node.attrs.update({"encoding-type": "csr_matrix", "encoding-version": "0.1.0", "shape": x.shape})
            nonzero = np.nonzero(x)
            node.create_dataset("data", data=x[nonzero], track_times=False)
            node.create_dataset("indices", data=nonzero[1].astype(np.int32), track_times=False)
            ptr = np.r_[0, np.cumsum(np.count_nonzero(x, axis=1))].astype(np.int64)
            node.create_dataset("indptr", data=ptr, track_times=False)


def make_inputs(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    genes = [f"SYN_G{i:03d}" for i in range(1, 6)]
    matrices = [np.array([[1, 0, 2, 0, 1], [0, 3, 1, 2, 0], [4, 1, 0, 1, 2], [2, 2, 1, 0, 1]], dtype=np.int32),
                np.array([[2, 0, 1, 3, 0], [1, 1, 0, 0, 4], [0, 2, 2, 1, 1], [3, 0, 1, 2, 2]], dtype=np.int32)]
    entries = []
    for label, matrix, encoding in zip(["SYN_A", "SYN_B"], matrices, ["dense", "csr_matrix"]):
        path = output / (label + ".h5ad")
        write_synthetic_h5ad(path, matrix, genes, encoding)
        entries.append({"label": label, "path": path.name, "sha256": sha256(path), "n_cells": 4,
                        "n_guides": 2, "cells_per_guide": 2,
                        "obs_ids_sha256": axis_digest([f"SYN_CELL_{i:04d}" for i in range(4)])})
    contract = {"schema": "DENG_NTC_CONTRACT_V1", "data_origin": "SYNTHETIC",
                "genes": genes, "panel": genes[:3], "contexts": entries}
    write_json(output / "contract.json", contract)
    return output / "contract.json", matrices


def run_demo(output):
    output = Path(output)
    require(not output.exists(), "output directory already exists")
    output.mkdir(parents=True, exist_ok=False)
    contract, matrices = make_inputs(output / "inputs")
    receipt = replay(contract, output / "replay")
    trace = trace_operator(matrices[0], [.2, -.3, .4, 0, -.1], matrices[0].mean(axis=0), np.ones(5, dtype=bool))
    master = [{"target_id": "OLD-SYN-1", "target_gene": "SYN_PANEL_1"}]
    migrated = migrate_ids(master, [{"old_id": "OLD-SYN-1", "new_id": "DENG-SYN-1"}])
    catalog = external_catalog([{"ensembl_id": "SYN_EXT_1", "target_gene": "SYN_RESEARCH_1"}], migrated)
    row = {"dataset": "SYNTHETIC", "job_id": "SYN_JOB", "context": "SYN_A",
           "evidence_target_id": catalog[0]["evidence_target_id"], "metric": "MSE",
           "value": None, "value_status": "AGGREGATE_ONLY_RATIO_OF_SUMS", "direction": "minimize",
           "axis_hash": axis_digest(["SYN_G001"]), "split_status": "SYNTHETIC_ONLY"}
    summary = {"data_origin": "SYNTHETIC", "fingerprint_rows": receipt["fingerprint_rows"],
               "panel_context_rows": receipt["panel_context_rows"],
               "decomposition": decompose([2, -1, 0, 1], [-1, 1, 3, -1], np.array([True, False, True, False])),
               "operator_Y": trace["Y"].tolist(),
               "operator_conserves_umi": bool(np.array_equal(trace["Y"].sum(axis=1), matrices[0].sum(axis=1))),
               "counts_stage_comparison": compare_effects((trace["Z"] - trace["X"]).ravel(), (trace["Y"] - trace["X"]).ravel()),
               "association": residual_rank_association([1, 2, 2, 4, 5, 6], [3, 1, 2, 6, 4, 5]),
               "master_example": migrated, "external_catalog": catalog,
               "evidence_check": validate_evidence([row], catalog)}
    write_json(output / "method_demo.json", summary)
    return summary

