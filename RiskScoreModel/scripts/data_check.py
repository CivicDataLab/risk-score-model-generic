import pandas as pd
import numpy as np
import os

# ----------------------------
# CONFIG
# ----------------------------

DATA_FOLDER = "data"
INPUT_FILE = "MASTER_VARIABLES.csv"

INPUT_VARS = [
    "mean_sex_ratio",
    "schools_count",
    "health_centres_count",
    "rail_length",
    "road_length",
    "net_sown_area_in_hac",
    "avg_electricity",
    "rc_piped_hhds_pct",
    "rc_nosanitation_hhds_pct",
    "sum_aged_population",
    "Embankment breached"
]

OUTPUT_VARS = [
    "Human_Live_Lost",
    "Population_affected_Total",
    "Crop_Area",
    "Embankments affected",
    "Roads",
    "Bridge"
]

DENOMINATORS = [
    "sum_population",
    "rc_area",
    "net_sown_area_in_hac"
]

ID_COL = "object_id"
TIME_COL = "timeperiod"

# ----------------------------
# LOAD DATA
# ----------------------------

path = os.path.join(os.getcwd(), DATA_FOLDER, INPUT_FILE)
df = pd.read_csv(path)

print("\nLoaded:", path)
print("Rows:", len(df))
print("Columns:", len(df.columns))

dea_vars = INPUT_VARS + OUTPUT_VARS

# ----------------------------
# CHECK NaN VALUES
# ----------------------------

print("\nChecking NaN values")

nan_counts = df[dea_vars].isnull().sum()

if nan_counts.sum() == 0:
    print("✓ No NaN values")
else:
    print("NaN detected:")
    print(nan_counts[nan_counts > 0])

# ----------------------------
# CHECK INFINITE VALUES
# ----------------------------

print("\nChecking infinite values")

inf_counts = np.isinf(df[dea_vars]).sum()

if inf_counts.sum() == 0:
    print("✓ No infinite values")
else:
    print("Infinite values detected:")
    print(inf_counts[inf_counts > 0])

# ----------------------------
# CHECK NEGATIVE VALUES
# ----------------------------

print("\nChecking negative values")

for col in dea_vars:
    neg = (df[col] < 0).sum()
    if neg > 0:
        print(f"{col}: {neg} negative values")

# ----------------------------
# CHECK ZERO ROWS
# ----------------------------

print("\nChecking rows with all zeros")

zero_rows = (df[dea_vars].sum(axis=1) == 0).sum()

print("Rows with all zeros:", zero_rows)

# ----------------------------
# CHECK DUPLICATE DMUs
# ----------------------------

print("\nChecking duplicate DMU identifiers")

duplicates = df.duplicated(subset=[ID_COL, TIME_COL]).sum()

print("Duplicate (object_id, timeperiod):", duplicates)

# ----------------------------
# CHECK ZERO VARIANCE
# ----------------------------

print("\nChecking zero variance columns")

for col in dea_vars:
    if df[col].std() == 0:
        print("No variation in:", col)

# ----------------------------
# CHECK EXTREME VALUES
# ----------------------------

print("\nChecking extreme values")

for col in dea_vars:
    max_val = df[col].max()
    if max_val > 1e9:
        print(f"{col} has very large values:", max_val)

# ----------------------------
# NEW: CHECK DENOMINATORS
# ----------------------------

print("\nChecking denominator columns")

for col in DENOMINATORS:

    zeros = (df[col] == 0).sum()
    nans = df[col].isnull().sum()

    print(f"\n{col}")
    print("zero values:", zeros)
    print("NaN values:", nans)

# ----------------------------
# NEW: SIMULATE DIVISION RISKS
# ----------------------------

print("\nChecking potential division-by-zero problems")

if "sum_population" in df.columns:
    bad = (df["sum_population"] == 0).sum()
    if bad > 0:
        print("Population denominators zero:", bad)

if "rc_area" in df.columns:
    bad = (df["rc_area"] == 0).sum()
    if bad > 0:
        print("Area denominators zero:", bad)

if "net_sown_area_in_hac" in df.columns:
    bad = (df["net_sown_area_in_hac"] == 0).sum()
    if bad > 0:
        print("Crop denominators zero:", bad)

# ----------------------------
# CHECK MONTHLY DEA FEASIBILITY
# ----------------------------

print("\nChecking monthly DEA feasibility")

for month in df[TIME_COL].unique():

    sub = df[df[TIME_COL] == month]

    if len(sub) < 5:
        print(f"{month}: Too few DMUs ({len(sub)})")

    if sub[dea_vars].isnull().any().any():
        print(f"{month}: NaN values present")

    if np.isinf(sub[dea_vars]).any().any():
        print(f"{month}: infinite values present")

print("\nDEA data check finished.")