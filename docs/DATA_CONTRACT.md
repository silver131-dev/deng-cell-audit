# Local data contract

`python -m deng_cell_audit demo --out results/demo` generates a complete working example at `results/demo/inputs/contract.json`. Use that generated structure as the reference; its hashes refer only to its generated synthetic files.

| Field | Requirement |
| --- | --- |
| schema | `DENG_NTC_CONTRACT_V1` |
| data_origin | Caller-supplied description; never treated as a verified publisher statement |
| genes | Ordered, distinct, nonempty full gene axis |
| panel | Ordered distinct subset of genes |
| gene_column | Optional var column; default `_index` resolves var's index attribute |
| contexts | Nonempty array with distinct context labels |
| contexts[].label | A nonempty context label |
| contexts[].path | Relative local H5AD path within the contract directory |
| contexts[].sha256 | Expected file SHA-256; checked before and after scanning |
| contexts[].n_cells | Positive integer, at most 2,000,000 |
| contexts[].n_guides | Positive integer |
| contexts[].cells_per_guide | Positive integer; product with n_guides must equal n_cells |
| contexts[].obs_ids_sha256 | SHA-256 of ordered UTF-8 observation IDs, joined by LF with one trailing LF |

Every H5AD needs `X`, `obs`, and `var`. Observation index values must be unique and match the cell-order digest. `obs/target_gene` must contain only `non-targeting`; `obs/ntc_id` must match the declared balanced distribution. Gene order must match exactly.

The reader validates CSR pointer lengths, monotonicity, index range, and strictly increasing unique column indices within each row. It does not repair malformed arrays or silently convert CSC. It does not choose a cell subset.

Hash values should be established and reviewed before a replay. Generating a new contract from whatever file happens to be present only records that file's identity; it is not independent source verification.

## Outputs

| Output | Contents |
| --- | --- |
| fingerprint.csv | One row per context × full-axis gene |
| panel_context.csv | Panel order × context order; raw mean, CPM, detection, zero fraction, classes |
| receipt.json | Contract/input/output/code hashes, runtime, dimensions, guide counts, chunk coverage, status |

No cell-level rows are exported. Nonetheless, statistics and hashes from real inputs remain research outputs whose distribution must be considered separately from this code. The project's MIT grant does not license those outputs. Before any real NTC table is added to a release, complete the separate review in [Data and third-party rights](../DATA_AND_THIRD_PARTY_RIGHTS.md). `data/`, `private/`, and `results/` are excluded from the release file list.

CSV files use UTF-8 and CRLF. Numeric exactness means parsed floating-point equality; byte equality additionally depends on serialization. A successful exit reports completed computation, not publisher authentication or model-use authorization. A failure after output creation leaves a failure receipt; use a new output path after correcting the cause.

