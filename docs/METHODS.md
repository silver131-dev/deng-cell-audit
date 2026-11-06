# Methods and limits

## Control statistics

For a context with n cells and G genes, use the complete supplied axis:

```text
L_i = sum_g X_ig
raw_mean_g = sum_i X_ig / n
detection_g = count_i(X_ig > 0) / n
mean_cp10k_g = sum_i(10000 * X_ig / L_i) / n
mean_cpm_g = 100 * mean_cp10k_g
zero_fraction_g = 1 - detection_g
```

Per-cell normalization precedes averaging. Pooled-count normalization and a panel-only denominator are different estimators. No log transform, feature filtering, imputation, batch correction, or model fitting occurs here.

Counts must be finite, nonnegative integers within int32 range. Raw sums use int64 with overflow checks; normalized sums use float64. Zero-library cells are rejected. Reduction order is fixed to 256 rows per chunk. Changing chunks, cell order, dependencies, or floating-point arithmetic can change serialized numbers; this package does not silently assign an acceptance tolerance.

CPM classes use boundaries 1 and 10. Detection classes use detection ≥0.8, then zero fraction ≥0.7, then the intermediate range. These are descriptive historical rule boundaries, not biological thresholds.

## Count-space operator

For caller-supplied effect d, boolean allowed mask M, nonnegative control reference c, and alpha:

```text
requested = alpha * d, with excluded coordinates set to zero
active = coordinates with abs(requested) > 1e-12
c0 = max(c, 0.25)
d0 = clip(requested, -2, 2)
f = clip(1 + expm1(d0) * (1 + 1/c0), 0.05, exp(2))
W_ig = X_ig * f_g on active coordinates
Z_i,active = W_i,active * sum(X_i,active) / sum(W_i,active)
Y = floor(Z), then allocate remaining UMI by descending fractional remainder
```

Ties in the final allocation preserve gene order. A zero active pool is unchanged. Excluded coordinates and input zeros are preserved; row UMI is conserved. This constrains the transformed counts but does not preserve effect L1/L2 mass. The returned W/Z/Y arrays allow the caller to inspect each stage.

The mask is supplied explicitly; no gene-name guessing or automatic cross-background alignment is implemented. This API is an audit component, not an end-to-end Final prediction runner.

## Stored-vector L1 partition

Let u=c+s, where s is already in the caller's intended stored/post-cis state:

```text
B = ||c||_1 + ||s||_1
C_cancel = sum_g(|c_g| + |s_g| - |u_g|)
E_mask = sum_excluded |u_g|
K = sum_kept |u_g|
B = C_cancel + E_mask + K
```

The implementation calculates the coordinate sums independently. Fractions are undefined (JSON null) when B=0. Complete cancellation with B>0 instead has a defined kept fraction of zero. This identity does not establish that a mask is biologically correct. No source variance, reliability tier, or transfer score is inferred.

## Rank-residual association

Apply average ranks to x, y, and each covariate. Regress ranked x/y on an intercept and ranked covariates, then calculate Pearson correlation of the residuals without reranking them. Rank-deficient designs, insufficient residual dimension, constant variables, and negligible residual variance yield an explicit undefined result.

The no-covariate result agrees with Spearman correlation. This component does not implement the archived multi-model bootstrap, permutation inference, target selection, or independent evaluation design.

## Evidence links

Aliases must be bijective and cover every supplied master ID. Original IDs remain in `historical_target_id`. External research records use their own key; unmatched symbols retain a null registry link. Exact supplied-symbol matching does not resolve HGNC synonyms or establish a biological equivalence.

Per-target metric slots distinguish observed, aggregate-only, not emitted, and undefined. Only observed slots carry a numeric value. Ratio-of-sums aggregate metrics must not be copied into per-target slots.

## Provenance of this implementation

The numerical definitions were reviewed against the project's archived NTC replay, Phase 2A decomposition, Common Driver rank analysis, and operator-audit specification. This release refactors those components and adds an explicit user-supplied H5AD contract. Embedded reference arrays, original data pins, real results, cell rosters, and private account links were not carried over.

Original WSL NTC replay and this package are distinct software versions. Historical raw-mean/detection agreement and small CPM differences do not prove that this release exactly reproduces the missing historical writer. Its current validation is described separately in [VALIDATION.md](VALIDATION.md).

The H5AD subset follows the [AnnData on-disk specification](https://anndata.readthedocs.io/en/stable/fileformat-prose.html). Dense arrays, CSR, categorical strings, and nonmissing nullable strings are supported. CSC and missing observation metadata are rejected. This is not a general AnnData reader.

