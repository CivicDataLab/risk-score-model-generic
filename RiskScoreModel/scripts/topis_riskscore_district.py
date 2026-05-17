import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from topsis import Topsis
import pandas as pd
import numpy as np
import glob
from config.loader import load_config

_RISKMODEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

cfg = load_config("topsis_config")

weights = [
    cfg["weights"]["flood_hazard"],
    cfg["weights"]["exposure"],
    cfg["weights"]["vulnerability"],
    cfg["weights"]["government_response"],
]
n_bins           = cfg["classification"]["n_bins"]
cumulative_vars  = cfg["cumulative_vars"]["variables"]
indicators       = list(cfg["indicators"].keys())
aggregation_rules = cfg["indicators"]
rounding_rules   = cfg["rounding"]

data_dir         = os.path.join(_RISKMODEL_DIR, cfg["paths"]["data_folder"])
assets_dir       = os.path.join(_RISKMODEL_DIR)

## INPUT: merge all factor score files
factor_files = glob.glob(os.path.join(_RISKMODEL_DIR, "data", "factor_scores_l1*.csv"))

factors            = ["exposure", "flood-hazard", "vulnerability", "government-response"]
additional_columns = [
    "financial_year", "efficiency", "flood-hazard-float",
    "total_tenders_hist", "SDRF_sanctions_hist", "other_tenders_hist",
]

merged_df = pd.read_csv(factor_files[0])
for path in factor_files[1:]:
    df = pd.read_csv(path)
    selected          = [c for c in factors if c in df.columns]
    selected_extra    = [c for c in additional_columns if c in df.columns]
    df = df[selected + ["object_id", "timeperiod"] + selected_extra]
    merged_df = pd.merge(
        merged_df, df, on=["object_id", "timeperiod"], how="inner", suffixes=("", "_drop")
    )
    merged_df = merged_df.loc[:, ~merged_df.columns.str.endswith("_drop")]

merged_df.sort_values(by=["object_id", "financial_year", "timeperiod"], inplace=True)

for var in cumulative_vars:
    if var in merged_df.columns:
        merged_df[var + "_fy_cumsum"] = merged_df.groupby(
            ["object_id", "financial_year"]
        )[var].cumsum()

df_months = []
for month in merged_df.timeperiod.unique():
    df_month         = merged_df[merged_df.timeperiod == month]
    evaluation_matrix = np.array(
        df_month[["flood-hazard", "exposure", "vulnerability", "government-response"]].values
    )
    criterias = [True, True, True, True]

    t = Topsis(evaluation_matrix, weights, criterias)
    t.calc()
    df_month = df_month.copy()
    df_month["TOPSIS_Score"] = t.worst_similarity
    df_month = df_month.sort_values(by="TOPSIS_Score", ascending=False)

    compscore            = pd.cut(df_month["TOPSIS_Score"], bins=n_bins, precision=0,
                                  labels=list(range(1, n_bins + 1)))
    df_month["risk-score"] = compscore
    df_months.append(df_month)

topsis = pd.concat(df_months)
topsis.columns = [col.lower().replace("_", "-").replace(" ", "-") for col in topsis.columns]

topsis.to_csv(os.path.join(_RISKMODEL_DIR, cfg["paths"]["output_file"]), index=False)

## DISTRICT LEVEL SCORES
dist_ids = pd.read_csv(os.path.join(_RISKMODEL_DIR, cfg["paths"]["district_lookup_file"]))

compositescorelabels = [str(i) for i in range(1, n_bins + 1)]


def _district_factor_score(topsis_df, col):
    dist = topsis_df.groupby(["district", "timeperiod"])[col].mean().reset_index()
    dist[col] = pd.cut(dist[col], bins=n_bins, precision=0, labels=compositescorelabels)
    return dist.merge(dist_ids, on="district")


dist_vul  = _district_factor_score(topsis, "vulnerability")
dist_exp  = _district_factor_score(topsis, "exposure")
dist_govt = _district_factor_score(topsis, "government-response")
dist_haz  = _district_factor_score(topsis, "flood-hazard")

topsis["risk-score"] = topsis["risk-score"].astype(int)
dist_risk = topsis.groupby(["district", "timeperiod"])["risk-score"].mean().reset_index()
dist_risk["risk-score"] = pd.cut(
    dist_risk["risk-score"], bins=n_bins, precision=0, labels=compositescorelabels
)
dist_risk = dist_risk.merge(dist_ids, on="district")

# Only aggregate indicators that are present in the data
present_indicators = [c for c in indicators if c in topsis.columns]
present_agg_rules  = {k: v for k, v in aggregation_rules.items() if k in topsis.columns}

dist_indicators = topsis.groupby(["district", "timeperiod"]).agg(present_agg_rules).reset_index()

dist = pd.concat(
    [
        dist_vul.set_index(["district", "timeperiod"]),
        dist_exp.set_index(["district", "timeperiod"])["exposure"],
        dist_govt.set_index(["district", "timeperiod"])["government-response"],
        dist_haz.set_index(["district", "timeperiod"])["flood-hazard"],
        dist_risk.set_index(["district", "timeperiod"])["risk-score"],
        dist_indicators.set_index(["district", "timeperiod"])[present_indicators],
    ],
    axis=1,
).reset_index()

final = pd.concat([topsis, dist], ignore_index=True)


def apply_rounding_rules(df, rules):
    for column, decimals in rules.items():
        if column in df.columns:
            df[column] = df[column].round(decimals)
    return df


final = apply_rounding_rules(final, rounding_rules)
final["inundation-pct"] = final["inundation-pct"] * 100
final["total-infrastructure-damage"] = (
    final["total-house-fully-damaged"] + final["roads"] + final["bridge"]
)
final.rename(
    columns={
        "preparedness-measures-tenders-awarded-value": "restoration-measures-tenders-awarded-value",
        "mean-sexratio": "sexratio",
    },
    inplace=True,
)

final.to_csv(os.path.join(_RISKMODEL_DIR, cfg["paths"]["final_output_file"]), index=False)
print("Risk score computation complete.")
