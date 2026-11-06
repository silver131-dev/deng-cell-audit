"""Shared input validation. No rounding or missing-value imputation."""
import numpy as np


def require(condition, message):
    if not condition:
        raise ValueError(message)


def counts(value):
    a = np.asarray(value)
    require(a.ndim == 2 and min(a.shape) > 0, "counts must be a nonempty matrix")
    require(a.dtype.kind in "iuf", "counts must be real numeric values")
    require(np.isfinite(a).all(), "counts contain nonfinite values")
    require(np.all(a >= 0) and np.all(a <= 2**31 - 1), "counts outside int32 range")
    require(np.array_equal(a, np.rint(a)), "counts must be integers, without rounding")
    require(a.size <= np.iinfo(np.int64).max // (2**31 - 1), "int64 sum bound exceeded")
    return a.astype(np.int64)


def names(values, label):
    result = list(values)
    require(bool(result) and all(isinstance(x, str) and x.strip() and not any(c in x for c in "\n\r\t") for x in result), f"invalid {label}")
    require(len(result) == len(set(result)), f"duplicate {label}")
    return result


def vector(value, label):
    a = np.asarray(value, dtype=np.float64)
    require(a.ndim == 1 and a.size > 0 and np.isfinite(a).all(), f"invalid {label}")
    return a

