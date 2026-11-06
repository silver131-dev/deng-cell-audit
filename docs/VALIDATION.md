# Validation record

Candidate: 0.1.0rc3. Review date: 2026-11-06.

## Local checks

| Check | Result | Scope |
| --- | --- | --- |
| Automated tests | 49 passed, zero skipped | Numerical identities, malformed counts/axes, CSR/dense, guide and hash guards, output refusal, CLI, identifier/null handling, release selection, false license metadata and omitted-notice rejection |
| Synthetic CLI demo | PASS | 8 artificial cells, 5 genes; 10 fingerprint rows and 6 panel-context rows |
| Archived-function comparison | PASS, retained from rc1 | 50 synthetic cases each for the NTC accumulator, L1 decomposition, and rank-residual association; those algorithms remain byte-identical in rc3 |
| Extracted source archive | PASS | Fresh ZIP extraction; manifest verified and the extracted 49-test suite run against the installed rc3 wheel |
| Wheel and source distribution | PASS | Both build successfully; wheel installed and run outside the source tree in an isolated Linux Python 3.12 environment, 49 tests and demo pass; source distribution contains all 36 reviewed files |
| License delivery and metadata | PASS | SPDX MIT, author ARiN, and complete LICENSE/data-rights notice verified in wheel and source distribution |
| Naming and entry points | PASS | Distribution `deng-cell-audit`, module `deng_cell_audit`, author ARiN, version `0.1.0rc3`, and canonical project/command in help verified; both the console command and `python -m deng_cell_audit` checked |
| Reviewed release files | PASS | 36 explicitly selected text files; byte hashes, UTF-8/syntax, selected sensitive-pattern checks, local Markdown links, and workflow YAML structure |
| Remote GitHub Actions | NOT RUN | Workflow configured; no repository or remote CI result is claimed |

Local environment: Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, h5py 3.16.0, HDF5 2.0.0, pytest 9.0.2, build 1.4.0, setuptools 84.2.1. Version pins are in requirements-tested.txt; they are not a full transitive or cross-platform hash lock. Python 3.13 is configured for remote CI but has not been run locally.

The final packaging pass updates this validation record and refreshes the per-file manifest; all other reviewed files match the tested archive. Numerical source files remain unchanged from rc1/rc2; rc3 changes the package version and CLI help, with the installed wheel checked as above. The isolated environment was originally created without system packages for rc1 and reused with the same dependencies. Stale package metadata from a prior installation was removed before reinstalling rc3; exactly one installed distribution and matching metadata/module versions were verified before the final tests. The ZIP contains source, documentation, licenses/notices, tests, and workflow files; generated datasets, test outputs, wheels, and source-distribution archives are not bundled.

## What the checks establish

The tests include analytic per-cell normalization, integer sums exceeding int32, malformed/negative/nonfinite counts, multi-chunk CSR/dense agreement, zero-library rejection, cell/gene-order mismatches, missing metadata, explicit undefined ratios, stable integer allocation, protected coordinates, and UMI/support invariants. Association is compared with SciPy ranks/correlation and an independent projection calculation.

The developer-side archived-function comparison used generated numeric arrays only. The original private reference functions are not distributed, so that comparison is not a public end-to-end reproduction of archived observations. The distributed tests and demo are independently runnable without them.

The release scanner checks an explicit file list and selected patterns. It is not a universal secret detector, a copyright audit, or biological validation. No original competition data were read during the package's synthetic verification. No Final submission, score, or ranking was changed or obtained.

## Maintainer rerun

Run the commands in the README from the repository root. Keep outputs in a new ignored results directory. Any source change invalidates the release manifest and requires review before refreshing it. Original historical provenance and model-use decisions remain separate from successful tests.

## Implementation references

- [AnnData on-disk format](https://anndata.readthedocs.io/en/stable/fileformat-prose.html)
- [Python packaging metadata](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [GitHub Python CI guide](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [Checkout release history](https://github.com/actions/checkout/releases)
- [Setup Python release history](https://github.com/actions/setup-python/releases)

Workflow dependencies are pinned to reviewed upstream commit IDs, rather than moving major tags. No upstream source code is bundled.
