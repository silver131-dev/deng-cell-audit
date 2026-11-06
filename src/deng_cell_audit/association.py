"""Exploratory rank-residual association; no causal or predictive claim."""
import numpy as np
from .checks import require, vector


def average_ranks(values):
    x = vector(values, "rank data")
    order = np.argsort(x, kind="stable")
    ranks = np.empty(len(x), dtype=float)
    start = 0
    while start < len(x):
        stop = start + 1
        while stop < len(x) and x[order[stop]] == x[order[start]]:
            stop += 1
        ranks[order[start:stop]] = (start + stop + 1) / 2
        start = stop
    return ranks


def residual_rank_association(x, y, covariates=()):
    x, y = vector(x, "x"), vector(y, "y")
    require(x.shape == y.shape, "association axis mismatch")
    ranks = []
    for covariate in covariates:
        c = vector(covariate, "covariate")
        require(c.shape == x.shape, "covariate shape mismatch")
        ranks.append(average_ranks(c))
    rx, ry = average_ranks(x), average_ranks(y)
    design = np.column_stack([np.ones(len(x)), *ranks])
    response = np.column_stack([rx, ry])
    beta, _, rank, _ = np.linalg.lstsq(design, response, rcond=1e-12)
    residuals = response - design @ beta
    rss = np.sum(residuals**2, axis=0)
    tss = np.sum((response - response.mean(axis=0))**2, axis=0)
    defined = rank == design.shape[1] and len(x) > design.shape[1] + 1 and bool(np.all((tss > 0) & (rss > 1e-12 * tss)))
    coefficient = None
    if defined:
        a, b = residuals[:, 0], residuals[:, 1]
        a, b = a - a.mean(), b - b.mean()
        coefficient = float(np.clip(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)), -1, 1))
    return {"rank_residual_correlation": coefficient, "defined": bool(defined),
            "design_rank": int(rank), "design_columns": int(design.shape[1]),
            "residual_dimension": int(len(x) - rank),
            "x_rank_variance_fraction_remaining": float(rss[0] / tss[0]) if tss[0] > 0 else None,
            "y_rank_variance_fraction_remaining": float(rss[1] / tss[1]) if tss[1] > 0 else None}

