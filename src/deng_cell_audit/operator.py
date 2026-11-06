"""Bounded multiplicative counts operator with conserved active-pool UMI."""
import numpy as np
from .checks import counts, require, vector


def trace_operator(matrix, effect, control_reference, allowed, alpha=1.0):
    x = counts(matrix)
    d, c = vector(effect, "effect"), vector(control_reference, "control reference")
    m = np.asarray(allowed)
    require(d.shape == c.shape == m.shape == (x.shape[1],) and m.dtype == np.dtype(bool), "operator axis or mask mismatch")
    require(np.all(c >= 0) and np.isfinite(alpha) and alpha >= 0, "invalid reference or alpha")
    with np.errstate(over="ignore"):
        requested = alpha * d
    require(np.isfinite(requested).all(), "effect overflow")
    requested[~m] = 0
    active = np.flatnonzero(np.abs(requested) > 1e-12)
    bounded = np.clip(requested, -2.0, 2.0)
    reference = np.maximum(c, .25)
    scale = np.clip(1 + np.expm1(bounded) * (1 + 1 / reference), .05, np.exp(2.0))
    w, z, y = x.astype(np.float64), x.astype(np.float64), x.copy()
    budgets = x[:, active].sum(axis=1, dtype=np.int64)
    if len(active):
        w[:, active] *= scale[active]
        for i, budget in enumerate(budgets):
            if budget == 0:
                continue
            weights = w[i, active]
            quota = weights * (float(budget) / float(weights.sum()))
            require(np.isfinite(quota).all(), "invalid quota")
            allocation = np.floor(quota).astype(np.int64)
            remainder = int(budget - allocation.sum())
            require(0 <= remainder <= len(active), "invalid rounding remainder")
            order = np.argsort(-(quota - allocation), kind="stable")
            allocation[order[:remainder]] += 1
            z[i, active], y[i, active] = quota, allocation
    require(np.all(y <= 2**31 - 1), "output count exceeds int32")
    require(np.array_equal(y.sum(axis=1), x.sum(axis=1)), "UMI conservation failed")
    require(np.array_equal(y[:, ~m], x[:, ~m]), "excluded coordinates changed")
    require(np.all(y[x == 0] == 0), "zero-support invariant failed")
    return {"X": x, "W": w, "Z": z, "Y": y.astype(np.int32), "requested": requested,
            "bounded": bounded, "scale": scale, "active": active, "budgets": budgets}


def compare_effects(reference, output, tolerance=1e-12):
    a, b = vector(reference, "reference effect"), vector(output, "output effect")
    require(a.shape == b.shape and np.isfinite(tolerance) and tolerance >= 0, "comparison shape or tolerance")
    nonzero, emitted = np.abs(a) > tolerance, np.abs(b) > tolerance
    denominator = int(nonzero.sum())
    norm, output_norm, difference_norm = (float(np.linalg.norm(v)) for v in (a, b, b - a))
    require(np.isfinite([norm, output_norm, difference_norm]).all(), "effect norm overflow")
    return {"reference_nonzero_n": denominator,
            "collapse_to_zero_n": int(np.count_nonzero(nonzero & ~emitted)),
            "collapse_rate": float(np.count_nonzero(nonzero & ~emitted) / denominator) if denominator else None,
            "amplitude_ratio_L2": output_norm / norm if norm > tolerance else None,
            "relative_L2_deviation": difference_norm / norm if norm > tolerance else None,
            "ratio_status": "DEFINED" if norm > tolerance else "UNDEFINED_ZERO_REFERENCE"}

