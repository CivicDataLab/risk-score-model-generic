import os
import sys
import warnings

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm

from config.loader import load_config

warnings.filterwarnings("ignore")

_RISKMODEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_financial_year(timeperiod, start_month):
    year = int(timeperiod.split("_")[0])
    month = int(timeperiod.split("_")[1])
    if month >= start_month:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"


def calculate_govtresponse_scores(df, response_vars, classes):
    scaler = MinMaxScaler()
    df = df.copy()
    df[response_vars] = scaler.fit_transform(df[response_vars])
    df["_sum"] = df[response_vars].sum(axis=1)

    mean = df["_sum"].mean()
    std = df["_sum"].std()

    conditions = [
        df["_sum"] <= mean,
        (df["_sum"] > mean) & (df["_sum"] <= mean + std),
        (df["_sum"] > mean + std) & (df["_sum"] <= mean + 2 * std),
        (df["_sum"] > mean + 2 * std) & (df["_sum"] <= mean + 3 * std),
        df["_sum"] > mean + 3 * std,
    ]
    df["government-response"] = np.select(conditions, classes)
    return df


def main():
    cfg = load_config("govtresponse_config")

    response_vars = cfg["inputs"]["variables"]
    start_month = cfg["fiscal_year"]["start_month"]
    classes = cfg["classification"]["classes"]
    class_col = cfg["output"]["class_column"]
    fy_col = cfg["output"]["financial_year_column"]
    time_col = cfg["columns"]["time_column"]
    object_id_col = cfg["columns"]["object_id_column"]
    data_path = os.path.join(_RISKMODEL_DIR, cfg["paths"]["data_folder"])

    master_variables = pd.read_csv(os.path.join(data_path, cfg["paths"]["input_file"]))

    master_variables[fy_col] = master_variables[time_col].apply(
        lambda x: get_financial_year(x, start_month)
    )

    for var in response_vars:
        master_variables[var] = master_variables.groupby(
            [object_id_col, fy_col]
        )[var].cumsum()

    results = []
    for month in tqdm(master_variables[time_col].unique()):
        month_data = master_variables[
            master_variables[time_col] == month
        ][response_vars + [time_col, object_id_col]].copy()
        results.append(calculate_govtresponse_scores(month_data, response_vars, classes))

    govtresponse = pd.concat(results)
    master_variables = master_variables.merge(
        govtresponse[[time_col, object_id_col, class_col]],
        on=[time_col, object_id_col],
    )

    master_variables.to_csv(os.path.join(data_path, cfg["output"]["file"]), index=False)
    print("Results saved successfully!")


if __name__ == "__main__":
    main()
