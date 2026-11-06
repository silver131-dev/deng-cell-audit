# DENG Cell Audit

Offline tools for checking control-cell statistics, count transformations, stored-vector decompositions, and research-evidence links.

**Release candidate: v0.1.0-rc3.** Prepared for review on 2026-11-06. The project's original code, documentation, tests, and synthetic fixtures are licensed under [MIT](LICENSE), copyright 2026 ARiN. The repository has not been published. See [license decision](LICENSE_DECISION.md) and [data and third-party rights](DATA_AND_THIRD_PARTY_RIGHTS.md).

**DENG Cell Audit — by ARiN.** The project name is DENG Cell Audit; the author/copyright-holder name is ARiN. The distribution and CLI are `deng-cell-audit`, and the Python module is `deng_cell_audit`. See the [canonical naming table](docs/NAMING.md) for the intended GitHub namespace and release filenames.

[繁體中文](README.zh-TW.md) · [Methods](docs/METHODS.md) · [Data contract](docs/DATA_CONTRACT.md) · [Validation](docs/VALIDATION.md)

## What works

| Module | Input | Output |
| --- | --- | --- |
| NTC replay | Local dense/CSR H5AD plus explicit hashes and gene/cell axes | Full-axis raw mean, mean per-cell CP10K, detection, and panel-context statistics |
| Counts operator | Counts, effect, reference expression, boolean mask | Scaling, conserved quotas, integer counts, and intermediate arrays |
| Stored-vector decomposition | Common/specific vectors and boolean mask | Cancellation, excluded mass, kept mass, and explicit undefined ratios |
| Rank association | Numeric vectors and optional covariates | Correlation of rank residuals, design rank, and defined/undefined status |
| Evidence checks | Caller-supplied master, aliases, external targets, metrics | Unique ID migration, nullable registry links, and missingness validation |

The demo generates **8 artificial cells, 5 artificial genes, 2 contexts, and a 3-gene panel**: 10 fingerprint rows and 6 panel-context rows. It contains no biological observations and needs no account, API key, or dataset download.

## Quick start (Python 3.12, Linux or WSL)

Unzip the candidate and enter the directory containing this README:

```bash
cd deng-cell-audit
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tested.txt
python -m pip install -e . --no-deps
python -m pytest -q
python -m deng_cell_audit demo --out results/demo
```

The output directory must be new. Results include:

- `results/demo/replay/fingerprint.csv`
- `results/demo/replay/panel_context.csv`
- `results/demo/replay/receipt.json`
- `results/demo/method_demo.json`

Replaying user-supplied data uses an explicit contract:

```bash
python -m deng_cell_audit replay --contract data/contract.json --out results/local-replay
```

See the [contract specification](docs/DATA_CONTRACT.md) before using this command. Input hashes, dimensions, full gene order, cell-order digest, NTC labels, and guide balance must all match. A hash binds bytes to a supplied contract; it does not authenticate a publisher.

## Scientific scope

This package provides audit components developed during independent research on single-cell perturbation modeling and reproducible numerical analysis. It is a new modular implementation, not the historical submission program or recovered historical NTC writer. It does not include the frozen SourceBank, provider controls, M4 workbook, real TRAIN/E150 metrics, private report, or original execution receipts.

Synthetic checks validate numerical and engineering behavior. They do not establish biological reliability, unseen-target prediction, causal mechanisms, competitive performance, or complete historical reproducibility. The evidence helpers retain `HOLD`; decomposition ratios are not reliability scores.

The NTC reader uses fixed 256-row blocks. At 18,533 genes, the dense float64 array for one block alone is about 36.2 MiB; multiple arrays and HDF5 buffers add overhead. It does not load the complete counts matrix at once. The small operator API does hold its supplied arrays in memory and is not a full-scale submission runner.

## Development and release

```bash
python -m pytest -q
python tools/verify_release.py
python -m build --no-isolation
python tools/build_release.py --out dist/deng-cell-audit-v0.1.0-rc3.zip
```

The release archive is built from an explicit reviewed file list, not a recursive copy of a research workspace. GitHub Actions is configured for synthetic testing on Python 3.12 and 3.13; remote CI has not run yet. See [validation scope](docs/VALIDATION.md) and [release notes](RELEASE_NOTES.md).

The MIT grant covers this project's original software and accompanying materials. External libraries retain their own licenses. Provider data and statistics derived from real inputs are not licensed by this repository; any future real NTC table requires a separate documented redistribution review.

