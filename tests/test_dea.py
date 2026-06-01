"""Tests for the open-source Data Envelopment Analysis (DEA) implementation.

These exercise the textbook 5-DMU / 2-input / 1-output example and assert the
theoretical relationships between the CRS and VRS models and between their
primal (multiplier) and dual (envelopment) forms.
"""

import pytest

import scripts.dea as dea

# CBC LP precision with the big-M bound on u0/v0 is ~1e-4 in the worst case;
# 1e-3 is a safe, generous threshold for these comparisons.
TOL = 1e-3

DMUS = ["A", "B", "C", "D", "E"]
X = {"A": [4.0, 3.0], "B": [7.0, 3.0], "C": [8.0, 1.0],
     "D": [4.0, 2.0], "E": [2.0, 4.0]}
Y = {"A": [1.0], "B": [1.0], "C": [1.0], "D": [1.0], "E": [1.0]}


def test_crs_input_primal_equals_dual():
    primal = dea.CRS(DMUS, X, Y, "input", dual=False)
    dual = dea.CRS(DMUS, X, Y, "input", dual=True)
    for a, b in zip(primal["efficiency"], dual["efficiency"]):
        assert abs(a - b) < TOL


def test_crs_output_primal_equals_dual():
    op = dea.CRS(DMUS, X, Y, "output", dual=False)
    od = dea.CRS(DMUS, X, Y, "output", dual=True)
    for a, b in zip(op["efficiency"], od["efficiency"]):
        assert abs(a - b) < TOL


def test_crs_input_equals_output():
    # For CRS, input-oriented and output-oriented efficiencies coincide.
    primal = dea.CRS(DMUS, X, Y, "input", dual=False)
    op = dea.CRS(DMUS, X, Y, "output", dual=False)
    for a, b in zip(primal["efficiency"], op["efficiency"]):
        assert abs(a - b) < TOL


def test_vrs_input_primal_equals_dual():
    vp = dea.VRS(DMUS, X, Y, "input", dual=False)
    vd = dea.VRS(DMUS, X, Y, "input", dual=True)
    for a, b in zip(vp["efficiency"], vd["efficiency"]):
        assert abs(a - b) < TOL


def test_vrs_output_primal_equals_dual():
    vop = dea.VRS(DMUS, X, Y, "output", dual=False)
    vod = dea.VRS(DMUS, X, Y, "output", dual=True)
    for a, b in zip(vop["efficiency"], vod["efficiency"]):
        assert abs(a - b) < TOL


def test_vrs_dominates_crs():
    # The VRS frontier dominates the CRS frontier, so VRS >= CRS.
    crs = dea.CRS(DMUS, X, Y, "input", dual=False)
    vrs = dea.VRS(DMUS, X, Y, "input", dual=False)
    for c, v in zip(crs["efficiency"], vrs["efficiency"]):
        assert v >= c - TOL


def test_efficiencies_in_unit_interval():
    for series in [
        dea.CRS(DMUS, X, Y, "input", dual=False)["efficiency"],
        dea.CRS(DMUS, X, Y, "input", dual=True)["efficiency"],
        dea.VRS(DMUS, X, Y, "input", dual=False)["efficiency"],
    ]:
        for v in series:
            assert 0 <= v <= 1 + TOL


def test_all_zero_output_dmu_is_inefficient():
    # A DMU with all-zero outputs is legitimately fully inefficient (efficiency 0)
    # and must not raise (regression test for empty-objective handling).
    dmus = ["A", "B"]
    x = {"A": [1.0], "B": [1.0]}
    y = {"A": [1.0], "B": [0.0]}
    res = dea.CRS(dmus, x, y, "input", dual=False)
    eff = dict(zip(res["DMU"], res["efficiency"]))
    assert eff["B"] == pytest.approx(0.0, abs=TOL)
