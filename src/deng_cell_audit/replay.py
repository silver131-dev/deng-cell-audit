"""Offline replay from an explicit local contract. Never downloads data."""
import csv
import hashlib
import json
import platform
import re
from pathlib import Path
import numpy as np
from . import __version__
from .checks import names, require
from .h5ad import scan_h5ad
from .ntc import FP_FIELDS, PANEL_FIELDS, panel_rows


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def read_contract(path):
    path = Path(path)
    require(path.stat().st_size <= 4 << 20, "contract exceeds 4 MiB")
    contract = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    require(contract.get("schema") == "DENG_NTC_CONTRACT_V1", "unknown contract schema")
    genes = names(contract["genes"], "genes")
    require(len(genes) <= 1_000_000, "gene axis too large")
    panel = names(contract["panel"], "panel")
    require(set(panel) <= set(genes), "panel not contained in gene axis")
    entries = contract["contexts"]
    require(isinstance(entries, list) and entries, "contexts must be nonempty")
    names([e["label"] for e in entries], "contexts")
    root, paths = path.resolve().parent, []
    for entry in entries:
        relative = Path(entry["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "unsafe input path")
        source = (root / relative).resolve()
        require(source.is_relative_to(root) and source.is_file(), "input must be a local file within contract directory")
        for field in ("sha256", "obs_ids_sha256"):
            require(isinstance(entry[field], str) and re.fullmatch(r"[0-9a-f]{64}", entry[field]), "invalid SHA-256")
        for field in ("n_cells", "n_guides", "cells_per_guide"):
            require(type(entry[field]) is int and entry[field] > 0, "invalid expected dimension")
        require(entry["n_cells"] <= 2_000_000, "cell count exceeds supported bound")
        require(entry["n_cells"] == entry["n_guides"] * entry["cells_per_guide"], "guide dimensions disagree")
        paths.append(source)
    require(len(paths) == len(set(paths)), "same file assigned to multiple contexts")
    return contract, paths


def write_json(path, data):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def write_csv(path, rows, fields):
    with Path(path).open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def replay(contract_path, output):
    import h5py
    contract_path, output = Path(contract_path), Path(output)
    require(not output.exists(), "output directory already exists")
    contract_sha = sha256(contract_path)
    contract, paths = read_contract(contract_path)
    for entry, path in zip(contract["contexts"], paths):
        require(sha256(path) == entry["sha256"], "input SHA-256 mismatch")
    output.mkdir(parents=True, exist_ok=False)
    receipt = {"schema": "DENG_NTC_REPLAY_V1", "package_version": __version__, "status": "STARTED",
               "data_origin": contract.get("data_origin", "USER_SUPPLIED_UNVERIFIED_ORIGIN"),
               "data_origin_basis": "CALLER_DECLARATION_NOT_VERIFIED",
               "model_use": "HOLD", "publisher_attestation": "NOT_ESTABLISHED",
               "contract_sha256": contract_sha, "contexts": [],
               "runtime": {"python": platform.python_version(), "numpy": np.__version__,
                           "h5py": h5py.__version__, "hdf5": h5py.version.hdf5_version},
               "source_code_sha256": {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}}
    try:
        rows = []
        for entry, path in zip(contract["contexts"], paths):
            context_rows, audit = scan_h5ad(path, entry, contract["genes"], contract.get("gene_column", "_index"))
            rows.extend(context_rows)
            audit["input_sha256"] = entry["sha256"]
            receipt["contexts"].append(audit)
        for entry, path in zip(contract["contexts"], paths):
            require(sha256(path) == entry["sha256"], "input changed during replay")
        require(sha256(contract_path) == contract_sha, "contract changed during replay")
        selected = panel_rows(rows, contract["panel"], [e["label"] for e in contract["contexts"]])
        write_csv(output / "fingerprint.csv", rows, FP_FIELDS)
        write_csv(output / "panel_context.csv", selected, PANEL_FIELDS)
        receipt.update(status="COMPLETED", fingerprint_rows=len(rows), panel_context_rows=len(selected),
                       outputs={name: sha256(output / name) for name in ("fingerprint.csv", "panel_context.csv")})
    except Exception as error:
        receipt.update(status="FAILED", error_type=type(error).__name__, error=str(error))
        write_json(output / "receipt.json", receipt)
        raise
    write_json(output / "receipt.json", receipt)
    return receipt

