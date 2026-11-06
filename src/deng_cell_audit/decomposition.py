"""L1 partition of supplied stored vectors. Not a reliability estimator."""
import numpy as np
from .checks import require, vector


def decompose(common, specific, mask):
    c, s = vector(common, "common"), vector(specific, "specific")
    m = np.asarray(mask)
    require(c.shape == s.shape == m.shape and m.dtype == np.dtype(bool), "shape or boolean mask mismatch")
    u = c + s
    with np.errstate(over="ignore", invalid="ignore"):
        common_l1, specific_l1 = float(np.abs(c).sum()), float(np.abs(s).sum())
        b = common_l1 + specific_l1
        cancellation = float((np.abs(c) + np.abs(s) - np.abs(u)).sum())
        excluded, kept = float(np.abs(u[~m]).sum()), float(np.abs(u[m]).sum())
    require(np.isfinite([b, cancellation, excluded, kept]).all(), "decomposition overflow")
    return {"common_L1": common_l1, "specific_post_cis_L1": specific_l1,
            "B_total_L1": b, "C_cancel_L1": cancellation,
            "u_sum_L1": float(np.abs(u).sum()), "E_mask_L1": excluded, "Mu_kept_L1": kept,
            "C_over_B": cancellation / b if b > 0 else None,
            "E_mask_over_B": excluded / b if b > 0 else None,
            "kept_over_B": kept / b if b > 0 else None,
            "ratio_status": "DEFINED" if b > 0 else "UNDEFINED_B_ZERO"}

