import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import numpy as np
import pandas as pd

from config.loader import load_config
from scripts.topsis import Topsis


_RISKMODEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _district_factor_score(topsis_df, col, dist_ids, n_bins, labels):
    dist = topsis_df.groupby(["district", "timeperiod"])[col].mean().reset_index()
    dist[col] = pd.cut(dist[col], bins=n_bins, precision=0, labels=labels)
    return dist.merge(dist_ids, on="district")


def apply_rounding_rules(df, rules):
    for column, decimals in rules.items():
        if column in df.columns:
            df[column] = df[column].round(decimals)
    return df


def main():
    cfg = load_config("topsis_config")

    weights = [
        cfg["weights"]["flood_hazard"],
        cfg["weights"]["exposure"],
        cfg["weights"]["vulnerability"],
        cfg["weights"]["government_response"],
    ]
    n_bins = cfg["classification"]["n_bins"]
    cumulative_vars = cfg["cumulative_vars"]["variables"]
    indicators = list(cfg["indicators"].keys())
    aggregation_rules = cfg["indicators"]
    rounding_rules = cfg["rounding"]

    data_dir = os.path.join(_RISKMODEL_DIR, cfg["paths"]["data_folder"])

    factor_files = glob.glob(os.path.join(data_dir, "factor_scores_l1*.csv"))

    factors = ["exposure", "flood-hazard", "vulnerability", "government-response"]
    # Extra per-unit columns to carry through from the factor files (only those
    # actually present are kept), used downstream for display/diagnostics.
    additional_columns = ["financial_year", "efficiency", "flood-hazard-float"]

    merged_df = pd.read_csv(factor_files[0])
    for path in factor_files[1:]:
        df = pd.read_csv(path)
        selected = [c for c in factors if c in df.columns]
        selected_extra = [c for c in additional_columns if c in df.columns]
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

    dist_ids = pd.read_csv(os.path.join(_RISKMODEL_DIR, cfg["paths"]["district_lookup_file"]))
    compositescorelabels = [str(i) for i in range(1, n_bins + 1)]

    df_months = []
    for month in merged_df.timeperiod.unique():
        df_month = merged_df[merged_df.timeperiod == month]
        evaluation_matrix = np.array(
            df_month[["flood-hazard", "exposure", "vulnerability", "government-response"]].values
        )
        criterias = [True, True, True, True]

        t = Topsis(evaluation_matrix, weights, criterias)
        t.calc()
        df_month = df_month.copy()
        df_month["topsis_score"] = t.worst_similarity
        df_month = df_month.sort_values(by="topsis_score", ascending=False)

        compscore = pd.cut(
            df_month["topsis_score"], bins=n_bins, precision=0,
            labels=list(range(1, n_bins + 1)),
        )
        df_month["risk-score"] = compscore
        df_months.append(df_month)

    topsis_result = pd.concat(df_months)
    topsis_result.columns = [
        col.lower().replace("_", "-").replace(" ", "-") for col in topsis_result.columns
    ]

    topsis_result.to_csv(
        os.path.join(_RISKMODEL_DIR, cfg["paths"]["output_file"]), index=False
    )

    dist_vul = _district_factor_score(
        topsis_result, "vulnerability", dist_ids, n_bins, compositescorelabels
    )
    dist_exp = _district_factor_score(
        topsis_result, "exposure", dist_ids, n_bins, compositescorelabels
    )
    dist_govt = _district_factor_score(
        topsis_result, "government-response", dist_ids, n_bins, compositescorelabels
    )
    dist_haz = _district_factor_score(
        topsis_result, "flood-hazard", dist_ids, n_bins, compositescorelabels
    )

    topsis_result["risk-score"] = topsis_result["risk-score"].astype(int)
    dist_risk = (
        topsis_result.groupby(["district", "timeperiod"])["risk-score"]
        .mean()
        .reset_index()
    )
    dist_risk["risk-score"] = pd.cut(
        dist_risk["risk-score"], bins=n_bins, precision=0, labels=compositescorelabels
    )
    dist_risk = dist_risk.merge(dist_ids, on="district")

    present_indicators = [c for c in indicators if c in topsis_result.columns]
    present_agg_rules = {
        k: v for k, v in aggregation_rules.items() if k in topsis_result.columns
    }

    dist_indicators = (
        topsis_result.groupby(["district", "timeperiod"]).agg(present_agg_rules).reset_index()
    )

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

    final = pd.concat([topsis_result, dist], ignore_index=True)

    final = apply_rounding_rules(final, rounding_rules)

    # Optional, config-driven post-processing (see the [derivations] and [renames]
    # sections of the TOPSIS config). All of this is optional: a geography that
    # omits those sections — as the generic config does — is unaffected. Column
    # names refer to the post-rename kebab-case output columns. This keeps any
    # geography-specific display logic in that geography's own config rather than
    # hardcoded in the shared pipeline.
    derivations = cfg.get("derivations", {})
    # Scale a column in place by a constant factor (e.g. fraction -> percentage).
    for column, factor in derivations.get("scale", {}).items():
        if column in final.columns:
            final[column] = final[column] * factor
    # Create a new column as the row-wise sum of components, only when all are present.
    for new_column, components in derivations.get("sum", {}).items():
        if all(c in final.columns for c in components):
            final[new_column] = final[components].sum(axis=1)

    # Optional column renames; missing columns are ignored.
    final.rename(columns=cfg.get("renames", {}), inplace=True)

    final.to_csv(
        os.path.join(_RISKMODEL_DIR, cfg["paths"]["final_output_file"]), index=False
    )
    print("Risk score computation complete.")


if __name__ == "__main__":
    main()
