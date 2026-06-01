"""Shared helpers for the factor-scoring entry scripts.

Collects the boilerplate that the per-factor scripts (hazard, exposure,
vulnerability, government-response) otherwise repeat: silencing warnings,
locating the repository root, reading the master variables CSV, the per-month
scoring loop, and merging scores back before writing the output CSV. Also holds
the mean±std interval classifier shared by exposure and government-response.
"""

import os
import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm

warnings.filterwarnings("ignore")

RISKMODEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Output column names produced by the factor scripts and consumed by
# topsis_riskscore.py. These are a fixed internal contract between those scripts,
# NOT a geography knob: changing one here means changing it in the producing
# factor script and every consumer in TOPSIS together. They are deliberately not
# configurable, since nothing about a geography's input data depends on them.
# Display columns are kebab-cased on final write in TOPSIS.
HAZARD_CLASS_COL = "flood-hazard"
HAZARD_FLOAT_COL = "flood-hazard-float"
EXPOSURE_COL = "exposure"
VULNERABILITY_COL = "vulnerability"
EFFICIENCY_COL = "efficiency"
DAMAGE_SCORE_COL = "damage_score"
GOVTRESPONSE_COL = "government-response"
FINANCIAL_YEAR_COL = "financial_year"


def load_master(cfg):
    """Read the master variables CSV; return (df, data_path)."""
    data_path = os.path.join(RISKMODEL_DIR, cfg["paths"]["data_folder"])
    df = pd.read_csv(os.path.join(data_path, cfg["paths"]["input_file"]))
    return df, data_path


def score_by_month(master, value_vars, time_col, object_id_col, fn):
    """Apply ``fn`` to each month's [value_vars + keys] slice and concat results."""
    results = []
    for month in tqdm(master[time_col].unique()):
        month_data = master[master[time_col] == month][
            value_vars + [time_col, object_id_col]
        ].copy()
        results.append(fn(month_data))
    return pd.concat(results)


def merge_and_save(master, scored, keys, cols, out_path):
    """Merge selected ``cols`` from ``scored`` back onto ``master`` and write CSV."""
    merged = master.merge(scored[keys + cols], on=keys)
    merged.to_csv(out_path, index=False)
    return merged


def classify_std_intervals(df, value_vars, classes, out_col):
    """MinMaxScaler -> row sum -> mean±std interval bins.

    Shared by exposure and government-response. Assumes ``len(classes) == 5``,
    matching the existing model.
    """
    df = df.copy()
    df[value_vars] = MinMaxScaler().fit_transform(df[value_vars])
    s = df[value_vars].sum(axis=1)
    mean, std = s.mean(), s.std()
    conditions = [
        s <= mean,
        (s > mean) & (s <= mean + std),
        (s > mean + std) & (s <= mean + 2 * std),
        (s > mean + 2 * std) & (s <= mean + 3 * std),
        s > mean + 3 * std,
    ]
    df[out_col] = np.select(conditions, classes)
    return df
