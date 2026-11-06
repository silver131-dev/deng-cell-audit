import math
import numpy as np
import pytest
from scipy.stats import rankdata, spearmanr
from deng_cell_audit.ntc import CountAccumulator, summarize_counts, panel_rows, classes
from deng_cell_audit.decomposition import decompose
from deng_cell_audit.operator import trace_operator, compare_effects
from deng_cell_audit.association import average_ranks, residual_rank_association
from deng_cell_audit.evidence import migrate_ids, external_catalog, validate_evidence


def test_per_cell_normalization_has_analytic_answer():
    rows = summarize_counts([[1, 0, 1], [0, 9, 1]], ["SYN_1", "SYN_2", "SYN_3"])
    assert [r["mean_raw_counts"] for r in rows] == [.5, 4.5, 1]
    assert [r["mean_cp10k"] for r in rows] == [2500, 4500, 3000]
    assert [r["detection_fraction"] for r in rows] == [.5, .5, 1]
    assert rows[0]["mean_cp10k"] != 10000 / 12


def test_chunk_weight_and_int64_accumulation():
    x = np.tile([2**30, 1], (257, 1))
    a = CountAccumulator(2)
    a.add(x[:256]); a.add(x[256:])
    assert a.raw_sum[0] == 257 * 2**30
    assert a.n == 257
    expected = 10000.0 * 2**30 / (2**30 + 1)
    assert a.rows("SYN_A", ["A", "B"])[0]["mean_cp10k"] == pytest.approx(expected)
    with pytest.raises(ValueError):
        CountAccumulator(2).add(x)


@pytest.mark.parametrize("bad", [[[0, 0]], [[-1, 2]], [[.5, 1]], [[math.nan, 1]], [[math.inf, 1]], [[2**31, 1]], [[True, False]]])
def test_invalid_counts_are_rejected(bad):
    with pytest.raises(ValueError):
        summarize_counts(bad, ["A", "B"])


def test_panel_order_units_and_class_boundaries():
    rows = summarize_counts([[1, 0], [0, 9]], ["G1", "G2"], "SYN_A")
    selected = panel_rows(rows, ["G2", "G1"], ["SYN_A"])
    assert [r["target_gene"] for r in selected] == ["G2", "G1"]
    assert selected[0]["mean_cpm"] == 500000
    assert selected[0]["zero_fraction"] == .5
    assert classes(1, .8) == ("Medium (1–<10 CPM)", "High detection (≥80%)")
    assert classes(10, .3) == ("High (≥10 CPM)", "High zero (≥70%)")


def test_panel_duplicate_missing_or_reordered_context_fails():
    rows = summarize_counts([[1, 1]], ["G1", "G2"], "A")
    with pytest.raises(ValueError): panel_rows(rows * 2, ["G1"], ["A"])
    with pytest.raises(ValueError): panel_rows(rows, ["G3"], ["A"])
    other = [{**r, "context": "B"} for r in reversed(rows)]
    with pytest.raises(ValueError): panel_rows(rows + other, ["G1"], ["A", "B"])


def test_decomposition_hand_calculation_and_mask_distinction():
    result = decompose([2, -1, 0, 1], [-1, 1, 3, -1], np.array([True, False, False, False]))
    assert result["B_total_L1"] == 10
    assert result["C_cancel_L1"] == 6
    assert result["E_mask_L1"] == 3
    assert result["Mu_kept_L1"] == 1
    assert result["C_over_B"] + result["E_mask_over_B"] + result["kept_over_B"] == pytest.approx(1)


def test_zero_denominator_is_not_zero_effect_fraction():
    zero = decompose([0], [0], np.array([True]))
    cancelled = decompose([2], [-2], np.array([True]))
    assert zero["kept_over_B"] is None
    assert cancelled["kept_over_B"] == 0
    assert cancelled["C_over_B"] == 1
    assert compare_effects([0, 0], [1, 0])["amplitude_ratio_L2"] is None


@pytest.mark.parametrize("mask", [[1, 0], [True], [True, False, True]])
def test_decomposition_requires_exact_boolean_mask(mask):
    with pytest.raises(ValueError): decompose([1, 2], [3, 4], mask)


def test_operator_identity_uniform_scaling_and_zero_pool():
    x = np.array([[3, 1, 0], [0, 0, 4]])
    mask = np.array([True, True, False])
    for d in [[0, 0, 0], [.2, .2, 5]]:
        trace = trace_operator(x, d, [1, 1, 1], mask)
        np.testing.assert_array_equal(trace["Y"], x)
    assert trace["budgets"][1] == 0


def test_operator_random_umi_support_and_quota_invariants():
    rng = np.random.default_rng(137)
    for _ in range(25):
        x = rng.integers(0, 30, (7, 11), dtype=np.int32)
        effect = rng.normal(size=11)
        allowed = rng.random(11) > .25
        trace = trace_operator(x, effect, x.mean(axis=0), allowed, alpha=.5)
        y, z = trace["Y"], trace["Z"]
        np.testing.assert_array_equal(y.sum(axis=1), x.sum(axis=1))
        np.testing.assert_array_equal(y[:, ~allowed], x[:, ~allowed])
        assert np.all(y[x == 0] == 0)
        assert np.max(np.abs(y - z)) <= 1 + 1e-12
        assert y.dtype == np.int32


def test_operator_largest_remainder_hand_calculation():
    # c=1; weights=(1.5,1.5,6), budget=3; quotas=(.5,.5,2).
    t = trace_operator([[1, 1, 1]], [math.log(1.25), math.log(1.25), math.log(3.5)],
                       [1, 1, 1], np.ones(3, bool))
    # A tied residual count goes to the first coordinate in stable axis order.
    np.testing.assert_array_equal(t["Y"], [[1, 0, 2]])
    assert np.all(t["scale"] > 0)


def test_average_ranks_and_unadjusted_match_scipy():
    x, y = [1, 2, 2, 4, 5, 6], [3, 1, 2, 6, 4, 5]
    np.testing.assert_array_equal(average_ranks(x), rankdata(x))
    result = residual_rank_association(x, y)
    assert result["rank_residual_correlation"] == pytest.approx(spearmanr(x, y).statistic, abs=1e-14)


def test_partial_rank_matches_independent_projection():
    x, y, z = np.array([4, 1, 6, 2, 8, 7, 3, 5]), np.array([5, 2, 3, 7, 1, 6, 8, 4]), np.array([1, 1, 2, 2, 3, 3, 4, 4])
    design = np.column_stack([np.ones(8), rankdata(z)])
    projection = np.eye(8) - design @ np.linalg.pinv(design)
    residual = projection @ np.column_stack([rankdata(x), rankdata(y)])
    expected = np.corrcoef(residual.T)[0, 1]
    assert residual_rank_association(x, y, [z])["rank_residual_correlation"] == pytest.approx(expected, abs=1e-12)


def test_undefined_rank_cases():
    x = [1, 2, 3, 4, 5, 6]
    for y, covariates in [([1]*6, []), (x, [x]), (list(reversed(x)), [x, x])]:
        result = residual_rank_association(x, y, covariates)
        assert not result["defined"] and result["rank_residual_correlation"] is None
    with pytest.raises(ValueError): residual_rank_association(x, x, [[1, 2]])


def test_alias_and_external_foreign_keys_preserve_null():
    master = [{"target_id": "OLD1", "target_gene": "SYN_PANEL"}]
    migrated = migrate_ids(master, [{"old_id": "OLD1", "new_id": "DENG1"}])
    assert master[0]["target_id"] == "OLD1"
    catalog = external_catalog([{"ensembl_id": "SYN_EXT", "target_gene": "SYN_OTHER"}], migrated)
    assert catalog[0]["master471_target_id"] is None
    with pytest.raises(ValueError): migrate_ids(master, [{"old_id": "OTHER", "new_id": "DENG1"}])
    row = {"dataset": "SYN", "job_id": "J", "context": "C", "evidence_target_id": catalog[0]["evidence_target_id"],
           "metric": "MSE", "value": None, "value_status": "AGGREGATE_ONLY_RATIO_OF_SUMS", "direction": "minimize",
           "axis_hash": "a" * 64, "split_status": "SYNTHETIC_ONLY"}
    assert validate_evidence([row], catalog)["model_use"] == "HOLD"
    with pytest.raises(ValueError): validate_evidence([{**row, "value": 0}], catalog)
    with pytest.raises(ValueError): validate_evidence([row, row], catalog)
    with pytest.raises(ValueError): validate_evidence([{**row, "evidence_target_id": "orphan"}], catalog)

