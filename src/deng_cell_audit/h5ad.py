"""Read a bounded subset of AnnData HDF5: dense/CSR X and string metadata."""
from collections import Counter
import hashlib
import numpy as np
from .checks import names, require
from .ntc import CHUNK_ROWS, CountAccumulator


def text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    require(isinstance(value, str), "metadata value is not text")
    return value


def string_column(node):
    import h5py
    if isinstance(node, h5py.Dataset):
        require(node.ndim == 1, "string column is not a vector")
        return [text(x) for x in node[()]]
    encoding = text(node.attrs.get("encoding-type", ""))
    if encoding == "categorical":
        categories = names(string_column(node["categories"]), "categories")
        codes = np.asarray(node["codes"][()])
        require(codes.ndim == 1 and codes.dtype.kind in "iu", "invalid categorical codes")
        require(np.all(codes >= 0) and np.all(codes < len(categories)), "missing or out-of-range category")
        return [categories[int(i)] for i in codes]
    if encoding == "nullable-string-array":
        values, mask = string_column(node["values"]), np.asarray(node["mask"][()])
        require(mask.dtype == np.dtype(bool) and mask.shape == (len(values),) and not mask.any(), "missing nullable string")
        return values
    raise ValueError("unsupported string encoding: " + encoding)


def axis_digest(values):
    return hashlib.sha256(("\n".join(values) + "\n").encode()).hexdigest()


def scan_h5ad(path, entry, genes, gene_column="_index"):
    import h5py
    n, ng = entry["n_cells"], len(genes)
    with h5py.File(path, "r") as f:
        require(all(k in f for k in ("X", "obs", "var")), "X/obs/var missing")
        var_key = text(f["var"].attrs.get("_index", "_index")) if gene_column == "_index" else gene_column
        actual_genes = names(string_column(f["var"][var_key]), "H5AD genes")
        require(actual_genes == genes, "gene axis/order differs from contract")
        obs = f["obs"]
        obs_key = text(obs.attrs.get("_index", "_index"))
        ids = names(string_column(obs[obs_key]), "cell IDs")
        labels = string_column(obs["target_gene"])
        guides = string_column(obs["ntc_id"])
        require(len(ids) == len(labels) == len(guides) == n, "observation length mismatch")
        require(set(labels) == {"non-targeting"}, "non-NTC or missing label")
        require(all(guides), "empty guide ID")
        sizes = Counter(guides)
        require(len(sizes) == entry["n_guides"] and set(sizes.values()) == {entry["cells_per_guide"]}, "guide balance mismatch")
        require(axis_digest(ids) == entry["obs_ids_sha256"], "cell ID/order hash mismatch")
        x = f["X"]
        dense = isinstance(x, h5py.Dataset)
        if dense:
            require(x.shape == (n, ng), "dense X shape mismatch")
        else:
            require(text(x.attrs.get("encoding-type", "")) == "csr_matrix", "only dense or CSR X supported")
            require(tuple(x.attrs.get("shape", ())) == (n, ng), "CSR shape mismatch")
            require(all(k in x for k in ("indptr", "indices", "data")), "CSR arrays missing")
            require(all(x[k].ndim == 1 for k in ("indptr", "indices", "data")), "CSR arrays must be vectors")
            require(x["indptr"].dtype.kind in "iu" and x["indices"].dtype.kind in "iu", "noninteger CSR indices")
            ptr = np.asarray(x["indptr"][()])
            require(len(ptr) == n + 1 and int(ptr[0]) == 0, "invalid CSR indptr")
            require(np.all(ptr[1:] >= ptr[:-1]), "decreasing CSR indptr")
            require(int(ptr[-1]) == len(x["indices"]) == len(x["data"]), "CSR lengths disagree")
        acc, chunks = CountAccumulator(ng), []
        for start in range(0, n, CHUNK_ROWS):
            stop = min(n, start + CHUNK_ROWS)
            if dense:
                block = x[start:stop, :]
            else:
                lo, hi = int(ptr[start]), int(ptr[stop])
                indices, values = np.asarray(x["indices"][lo:hi]), np.asarray(x["data"][lo:hi])
                require(np.all(indices >= 0) and np.all(indices < ng), "CSR index out of range")
                block = np.zeros((stop - start, ng), dtype=values.dtype)
                for row in range(start, stop):
                    a, b = int(ptr[row]) - lo, int(ptr[row + 1]) - lo
                    cols = indices[a:b]
                    require(np.all(cols[1:] > cols[:-1]), "CSR duplicate or unsorted indices")
                    block[row - start, cols] = values[a:b]
            acc.add(block)
            chunks.append({"start": start, "stop_exclusive": stop})
        return acc.rows(entry["label"], genes), {
            "context": entry["label"], "shape": [n, ng], "encoding": "dense" if dense else "csr_matrix",
            "guide_count": len(sizes), "cells_per_guide": entry["cells_per_guide"],
            "total_umis": acc.total_umis, "nonzero_entries": int(acc.detected.sum()),
            "zero_library_cells": 0, "min_library": acc.min_library, "max_library": acc.max_library,
            "obs_ids_sha256": axis_digest(ids), "gene_axis_sha256": axis_digest(genes), "chunks": chunks,
        }

