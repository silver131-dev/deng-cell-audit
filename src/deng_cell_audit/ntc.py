"""Per-cell, full-axis control statistics. The row order is significant."""
import numpy as np
from .checks import counts, names, require

CHUNK_ROWS = 256
FP_FIELDS = ["context", "gene", "mean_raw_counts", "mean_cp10k", "detection_fraction"]
PANEL_FIELDS = ["target_order", "target_gene", "context", "mean_cpm", "detection_rate",
                "zero_fraction", "cpm_class", "detection_class", "mean_raw_counts"]


class CountAccumulator:
    def __init__(self, n_genes):
        require(isinstance(n_genes, int) and 0 < n_genes <= 1_000_000, "invalid gene count")
        self.n_genes = n_genes
        self.raw_sum = np.zeros(n_genes, dtype=np.int64)
        self.detected = np.zeros(n_genes, dtype=np.int64)
        self.cp10k_sum = np.zeros(n_genes, dtype=np.float64)
        self.n = 0
        self.total_umis = 0
        self.min_library = None
        self.max_library = None

    def add(self, block):
        a = counts(block)
        require(a.shape[1] == self.n_genes and a.shape[0] <= CHUNK_ROWS, "block shape or chunk limit")
        library = a.sum(axis=1, dtype=np.int64)
        require(np.all(library > 0), "zero-library cell")
        addition = a.sum(axis=0, dtype=np.int64)
        require(np.all(self.raw_sum <= np.iinfo(np.int64).max - addition), "gene sum overflow")
        require(self.n + len(a) <= np.iinfo(np.int64).max, "cell count overflow")
        self.raw_sum += addition
        self.detected += np.count_nonzero(a, axis=0)
        normalized = a.astype(np.float64)
        normalized *= 10000.0
        normalized /= library[:, None]
        self.cp10k_sum += normalized.sum(axis=0, dtype=np.float64)
        self.n += len(a)
        self.total_umis += int(library.sum(dtype=np.int64))
        lo, hi = int(library.min()), int(library.max())
        self.min_library = lo if self.min_library is None else min(self.min_library, lo)
        self.max_library = hi if self.max_library is None else max(self.max_library, hi)

    def rows(self, context, genes):
        genes = names(genes, "gene axis")
        names([context], "context")
        require(self.n > 0 and len(genes) == self.n_genes, "empty accumulator or axis mismatch")
        return [dict(zip(FP_FIELDS, [context, gene, float(self.raw_sum[j] / self.n),
                    float(self.cp10k_sum[j] / self.n), float(self.detected[j] / self.n)]))
                for j, gene in enumerate(genes)]


def summarize_counts(matrix, genes, context="SYN_A"):
    a = np.asarray(matrix)
    require(a.ndim == 2 and a.shape[0] > 0, "invalid count matrix")
    acc = CountAccumulator(a.shape[1])
    for start in range(0, len(a), CHUNK_ROWS):
        acc.add(a[start:start + CHUNK_ROWS])
    return acc.rows(context, genes)


def classes(cpm, detection):
    require(np.isfinite(cpm) and cpm >= 0 and np.isfinite(detection) and 0 <= detection <= 1, "invalid classification input")
    # Preserve the original zero-fraction arithmetic at the 0.30 boundary.
    return (
        "High (≥10 CPM)" if cpm >= 10 else "Medium (1–<10 CPM)" if cpm >= 1 else "Low (<1 CPM)",
        "High detection (≥80%)" if detection >= .8 else
        "High zero (≥70%)" if 1 - detection >= .7 else "Intermediate detection (30–<80%)",
    )


def panel_rows(fingerprint, panel, contexts):
    panel = names(panel, "panel")
    contexts = names(contexts, "contexts")
    index, axes = {}, {c: [] for c in contexts}
    for row in fingerprint:
        context, gene = row["context"], row["gene"]
        require(context in axes, "unexpected context")
        names([gene], "gene")
        key = (context, gene)
        require(key not in index, "duplicate fingerprint key")
        raw, cp10k, detection = (float(row[k]) for k in FP_FIELDS[2:])
        require(np.isfinite([raw, cp10k, detection]).all(), "nonfinite fingerprint")
        require(raw >= 0 and cp10k >= 0 and 0 <= detection <= 1, "invalid fingerprint")
        index[key] = (raw, cp10k, detection)
        axes[context].append(gene)
    require(bool(axes[contexts[0]]) and all(axes[c] == axes[contexts[0]] for c in contexts), "context gene order mismatch")
    result = []
    for order, gene in enumerate(panel, 1):
        for context in contexts:
            require((context, gene) in index, "panel gene missing from fingerprint")
            raw, cp10k, detection = index[context, gene]
            cpm = cp10k * 100.0
            labels = classes(cpm, detection)
            result.append(dict(zip(PANEL_FIELDS, [order, gene, context, cpm, detection,
                          1 - detection, *labels, raw])))
    return result

