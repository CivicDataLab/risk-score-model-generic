TOL = 1e-3  # CBC LP precision with the big-M bound on u0/v0 is ~1e-4 in
            # the worst case; 1e-3 is a safe, generous threshold for dea.
import sys
sys.path.insert(0, "/home/claude")

import csv
import os
import tempfile
import dea

# Textbook 5-DMU, 2-input, 1-output example.
dmus = ["A", "B", "C", "D", "E"]
X = {"A": [4.0, 3.0], "B": [7.0, 3.0], "C": [8.0, 1.0],
     "D": [4.0, 2.0], "E": [2.0, 4.0]}
Y = {"A": [1.0],     "B": [1.0],      "C": [1.0],
     "D": [1.0],     "E": [1.0]}

print("=== CRS input-oriented ===")
primal = dea.CRS(dmus, X, Y, "input", dual=False)
dual   = dea.CRS(dmus, X, Y, "input", dual=True)
print("primal:\n", primal)
print("dual:\n", dual)

# Primal == dual within tolerance
for a, b in zip(primal["efficiency"], dual["efficiency"]):
    assert abs(a - b) < TOL, f"primal/dual mismatch: {a} vs {b}"
print("OK: CRS input primal == dual")

print("\n=== CRS output-oriented ===")
op = dea.CRS(dmus, X, Y, "output", dual=False)
od = dea.CRS(dmus, X, Y, "output", dual=True)
print("primal:\n", op)
print("dual:\n", od)
for a, b in zip(op["efficiency"], od["efficiency"]):
    assert abs(a - b) < TOL, f"output primal/dual mismatch: {a} vs {b}"
print("OK: CRS output primal == dual")

# For CRS, input-oriented and output-oriented efficiencies are equal.
for a, b in zip(primal["efficiency"], op["efficiency"]):
    assert abs(a - b) < TOL, f"CRS input/output mismatch: {a} vs {b}"
print("OK: CRS input == CRS output (theory)")

print("\n=== VRS input-oriented ===")
vp = dea.VRS(dmus, X, Y, "input", dual=False)
vd = dea.VRS(dmus, X, Y, "input", dual=True)
print("primal:\n", vp)
print("dual:\n", vd)
for a, b in zip(vp["efficiency"], vd["efficiency"]):
    assert abs(a - b) < TOL, f"VRS input primal/dual mismatch: {a} vs {b}"
print("OK: VRS input primal == dual")

# VRS efficiency >= CRS efficiency (since VRS frontier dominates).
for a, b in zip(primal["efficiency"], vp["efficiency"]):
    assert b >= a - TOL, f"VRS < CRS: VRS={b}, CRS={a}"
print("OK: VRS >= CRS (theory)")

print("\n=== VRS output-oriented ===")
vop = dea.VRS(dmus, X, Y, "output", dual=False)
vod = dea.VRS(dmus, X, Y, "output", dual=True)
print("primal:\n", vop)
print("dual:\n", vod)
for a, b in zip(vop["efficiency"], vod["efficiency"]):
    assert abs(a - b) < TOL, f"VRS output primal/dual mismatch: {a} vs {b}"
print("OK: VRS output primal == dual")

# All efficiencies should be in (0, 1]
for series in [primal["efficiency"], dual["efficiency"], vp["efficiency"]]:
    for v in series:
        assert 0 < v <= 1 + TOL, f"out-of-range efficiency: {v}"
print("OK: all efficiencies in (0, 1]")

# CSV ingestion
print("\n=== CSV ingestion ===")
with tempfile.NamedTemporaryFile("w", newline="", suffix=".csv",
                                  delete=False) as fh:
    csv_path = fh.name
    w = csv.writer(fh)
    w.writerow(["DMU", "X1", "X2", "Y1"])
    for d in dmus:
        w.writerow([d, X[d][0], X[d][1], Y[d][0]])

try:
    d2, x2, y2 = dea.csv2dict(csv_path, in_range=[2, 3], out_range=[4, 4])
    assert d2 == dmus
    assert x2 == X
    assert y2 == Y
    print("OK: csv2dict round-trips")

    # Bad input: in_range starts at 0 -> should raise
    try:
        dea.csv2dict(csv_path, in_range=[0, 1], out_range=[3, 3])
    except ValueError:
        print("OK: csv2dict rejects 0-based indices")
    else:
        raise AssertionError("expected ValueError for in_range=[0,1]")
finally:
    os.unlink(csv_path)

print("\nAll tests passed.")
