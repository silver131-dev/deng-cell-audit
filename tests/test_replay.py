import json
import subprocess
import sys
import h5py
import numpy as np
import pytest
from deng_cell_audit.demo import make_inputs, run_demo, write_synthetic_h5ad
from deng_cell_audit.h5ad import scan_h5ad, string_column, axis_digest
from deng_cell_audit.ntc import summarize_counts
from deng_cell_audit.replay import read_contract, replay, sha256


@pytest.fixture
def inputs(tmp_path):
    path, matrices = make_inputs(tmp_path / "input")
    contract, paths = read_contract(path)
    return path, contract, paths, matrices


def test_dense_and_csr_full_replay_matches_independent_small_arrays(inputs, tmp_path):
    path, contract, paths, matrices = inputs
    result = replay(path, tmp_path / "out")
    assert result["status"] == "COMPLETED"
    assert result["fingerprint_rows"] == 10 and result["panel_context_rows"] == 6
    assert [c["encoding"] for c in result["contexts"]] == ["dense", "csr_matrix"]
    for entry, h5path, matrix in zip(contract["contexts"], paths, matrices):
        rows, audit = scan_h5ad(h5path, entry, contract["genes"])
        assert rows == summarize_counts(matrix, contract["genes"], entry["label"])
        assert audit["total_umis"] == int(matrix.sum())
        assert audit["chunks"] == [{"start": 0, "stop_exclusive": 4}]
    assert result["outputs"]["fingerprint.csv"] == sha256(tmp_path / "out/fingerprint.csv")


def test_hash_tamper_stops_before_output(inputs, tmp_path):
    path, contract, paths, matrices = inputs
    with paths[0].open("ab") as stream: stream.write(b"changed")
    with pytest.raises(ValueError, match="SHA"):
        replay(path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_existing_output_is_not_overwritten(inputs, tmp_path):
    out = tmp_path / "out"; out.mkdir(); sentinel = out / "keep.txt"; sentinel.write_text("keep")
    with pytest.raises(ValueError, match="exists"): replay(inputs[0], out)
    assert sentinel.read_text() == "keep"


@pytest.mark.parametrize("mutation", ["gene_order", "cell_order", "non_ntc", "guide_balance", "csc", "bad_index", "duplicate_index", "bad_pointer"])
def test_h5ad_structure_guards(inputs, mutation):
    _, contract, paths, _ = inputs
    entry, path = contract["contexts"][1], paths[1]
    with h5py.File(path, "r+") as f:
        if mutation == "gene_order": f["var/_index"][0] = "WRONG"
        elif mutation == "cell_order": f["obs/_index"][0] = "WRONG"
        elif mutation == "non_ntc": f["obs/target_gene"][0] = "targeted"
        elif mutation == "guide_balance": f["obs/ntc_id"][0] = "EXTRA_GUIDE"
        elif mutation == "csc": f["X"].attrs["encoding-type"] = "csc_matrix"
        elif mutation == "bad_index": f["X/indices"][0] = 100
        elif mutation == "duplicate_index": f["X/indices"][1] = f["X/indices"][0]
        elif mutation == "bad_pointer": f["X/indptr"][1] = 1000
    with pytest.raises(ValueError): scan_h5ad(path, entry, contract["genes"])


def test_missing_strings_and_invalid_categories_are_rejected(tmp_path):
    with h5py.File(tmp_path / "strings.h5", "w") as f:
        s = f.create_group("nullable"); s.attrs["encoding-type"] = "nullable-string-array"
        s.create_dataset("values", data=["SYN_A", "SYN_B"], dtype=h5py.string_dtype())
        s.create_dataset("mask", data=[False, True])
        with pytest.raises(ValueError): string_column(s)
        s["mask"][1] = False; assert string_column(s) == ["SYN_A", "SYN_B"]
        c = f.create_group("categorical"); c.attrs["encoding-type"] = "categorical"
        c.create_dataset("categories", data=["SYN_A", "SYN_B"], dtype=h5py.string_dtype())
        c.create_dataset("codes", data=[0, 1, 0]); assert string_column(c) == ["SYN_A", "SYN_B", "SYN_A"]
        c["codes"][1] = -1
        with pytest.raises(ValueError): string_column(c)


def test_failure_receipt_does_not_say_completed(inputs, tmp_path):
    path, contract, paths, _ = inputs
    with h5py.File(paths[0], "r+") as f: f["X"][0] = 0
    contract["contexts"][0]["sha256"] = sha256(paths[0]); path.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="zero-library"): replay(path, tmp_path / "failed")
    assert json.loads((tmp_path / "failed/receipt.json").read_text())["status"] == "FAILED"
    assert not (tmp_path / "failed/fingerprint.csv").exists()


def test_contract_path_and_duplicate_key_guards(inputs, tmp_path):
    path, contract, _, _ = inputs
    contract["contexts"][0]["path"] = "../outside.h5ad"; path.write_text(json.dumps(contract))
    with pytest.raises(ValueError): read_contract(path)
    path.write_text('{"schema":"x","schema":"y"}')
    with pytest.raises(ValueError, match="duplicate"): read_contract(path)


def test_demo_is_deterministic_and_preserves_null(tmp_path):
    a, b = run_demo(tmp_path / "a"), run_demo(tmp_path / "b")
    assert a == b
    assert a["decomposition"]["B_total_L1"] == 10
    assert a["operator_conserves_umi"]
    assert a["external_catalog"][0]["master471_target_id"] is None
    assert (tmp_path / "a/replay/fingerprint.csv").read_bytes() == (tmp_path / "b/replay/fingerprint.csv").read_bytes()


def test_installed_module_cli(tmp_path):
    output = tmp_path / "cli"
    run = subprocess.run([sys.executable, "-m", "deng_cell_audit", "demo", "--out", str(output)], text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["status"] == "COMPLETED"
    repeat = subprocess.run([sys.executable, "-m", "deng_cell_audit", "demo", "--out", str(output)], text=True, capture_output=True)
    assert repeat.returncode == 2


def test_multi_chunk_h5ad_csr_and_dense_agree(tmp_path):
    rng = np.random.default_rng(101)
    matrix = rng.integers(0, 8, (258, 5), dtype=np.int32)
    matrix[:, 0] += 1
    genes = [f"SYN_G{i}" for i in range(5)]
    entry = {"label": "SYN_C", "n_cells": 258, "n_guides": 129, "cells_per_guide": 2,
             "obs_ids_sha256": axis_digest([f"SYN_CELL_{i:04d}" for i in range(258)])}
    results = []
    for encoding in ["dense", "csr_matrix"]:
        path = tmp_path / (encoding + ".h5ad")
        write_synthetic_h5ad(path, matrix, genes, encoding)
        rows, audit = scan_h5ad(path, entry, genes)
        assert audit["chunks"] == [{"start": 0, "stop_exclusive": 256}, {"start": 256, "stop_exclusive": 258}]
        results.append(rows)
    assert results[0] == results[1]
    expected = (matrix / matrix.sum(axis=1)[:, None] * 10000).mean(axis=0)
    np.testing.assert_allclose([r["mean_cp10k"] for r in results[0]], expected, rtol=1e-14, atol=1e-12)

