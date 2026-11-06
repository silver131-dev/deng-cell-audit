# DENG Cell Audit v0.1.0-rc3

Prepared 2026-11-06. Draft prerelease notes; no GitHub Release has been created.

## Changes from rc2

- Document the distinct canonical project, author, package, module, CLI, and GitHub namespace in `docs/NAMING.md` and both READMEs.
- Retain DENG Cell Audit as the project name and ARiN as the confirmed author/copyright-holder name; the MIT grant is unchanged.
- Use `deng-cell-audit-v0.1.0-rc3.zip` consistently for the review download and prepared GitHub Release asset, with `deng-cell-audit/` as the extraction root.
- Synchronize the package version, prepared tag, workflow output, and publishing instructions. Existing imports, commands, schemas, and historical IDs remain compatible.
- Show the canonical project name and console command in CLI help.

## Licensing changes introduced in rc2

- Apply MIT to the original project materials with the owner-confirmed public copyright-holder name ARiN.
- Include the complete LICENSE and the data/third-party rights notice in source and wheel distributions; declare SPDX `MIT` in package metadata.
- Describe the research background in general terms, removing the competition name from the README.
- Document upstream dependency licenses and require a separate redistribution review before any real NTC statistics are included.
- Derive release version/license metadata from `pyproject.toml` and check it against the manifest.

Numerical algorithms, dependency versions, and scientific claims are unchanged.

## Included

- Offline dense/CSR H5AD control statistics with explicit input and axis hashes.
- Fixed 256-row accumulation, integer-count checks, and per-cell full-axis normalization.
- Count-space operator traces, stored-vector L1 partition, and rank-residual association.
- Bijection/foreign-key/missingness checks for caller-supplied research evidence.
- Synthetic end-to-end demo, automated tests, version pins, and GitHub Actions configuration.
- Reviewed-file packaging, content scanning, per-file SHA-256 manifest, and release instructions.

## Limits

The demo is synthetic. This is a refactored audit toolkit, not the competition submission, historical writer, full private M4 integration, or a rerun of the complete Common Driver inference workflow. No official Final score, ranking, or new biological performance is claimed.

The MIT license covers the project's original software and accompanying materials. External software retains its own licenses; real data, private reports, raw execution receipts, and frozen SourceBank files are not included. Full historical producer and official transport attestations remain unresolved in the private project record. See [Data and third-party rights](DATA_AND_THIRD_PARTY_RIGHTS.md).

Local validation and remote CI status are recorded separately in [docs/VALIDATION.md](docs/VALIDATION.md).

