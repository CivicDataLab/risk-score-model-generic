"""End-to-end smoke test for the full risk-score pipeline.

Regenerates the synthetic sample, then runs the four factor scripts and the
TOPSIS aggregation as subprocesses from the repository root (matching the
documented usage), and asserts that the expected outputs are produced with
valid columns and value ranges.
"""

import os
import subprocess
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def _run(script):
    subprocess.run(
        [sys.executable, os.path.join("scripts", script)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )


@pytest.fixture(scope="module")
def pipeline_outputs():
    _run("generate_sample_data.py")
    for script in ["hazard.py", "exposure.py", "vulnerability.py",
                   "govtresponse.py", "topsis_riskscore.py"]:
        _run(script)
    yield DATA


def _read(name):
    return pd.read_csv(os.path.join(DATA, name))


@pytest.mark.parametrize(
    "filename,column",
    [
        ("factor_scores_l1_flood-hazard.csv", "flood-hazard"),
        ("factor_scores_l1_exposure.csv", "exposure"),
        ("factor_scores_l1_vulnerability.csv", "vulnerability"),
        ("factor_scores_l1_government-response.csv", "government-response"),
    ],
)
def test_factor_scores_in_range(pipeline_outputs, filename, column):
    df = _read(filename)
    assert column in df.columns
    vals = df[column].dropna()
    assert len(vals) > 0
    assert vals.between(1, 5).all()


def test_vulnerability_efficiency_in_unit_interval(pipeline_outputs):
    df = _read("factor_scores_l1_vulnerability.csv")
    eff = df["efficiency"].dropna()
    assert eff.between(0, 1).all()


def test_block_risk_score(pipeline_outputs):
    rs = _read("risk_score.csv")
    # Columns are lower-cased / kebab-cased on write.
    assert "risk-score" in rs.columns
    assert "topsis-score" in rs.columns
    scores = rs["risk-score"].dropna()
    assert scores.between(1, 5).all()
    # The composite should exercise a real spread, not collapse to one class.
    assert scores.nunique() >= 3


def test_final_district_output(pipeline_outputs):
    final = _read("risk_score_district.csv")
    block = _read("risk_score.csv")
    # District-level rows are appended below the block-level rows.
    assert len(final) > len(block)
    # Block rows keep their kebab-case "object-id"; appended district rows do not.
    assert final["object-id"].notna().sum() > 0   # block-level rows present
    assert final["object-id"].isna().sum() > 0    # district-level rows appended
