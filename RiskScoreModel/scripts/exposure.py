import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm
import warnings
from config.loader import load_config

warnings.filterwarnings("ignore")

_RISKMODEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def calculate_exposure_scores(df, exposure_vars, classes):
    scaler = MinMaxScaler()
    df = df.copy()
    df[exposure_vars] = scaler.fit_transform(df[exposure_vars])
    df["_sum"] = df[exposure_vars].sum(axis=1)

    mean = df["_sum"].mean()
    std  = df["_sum"].std()

    conditions = [
        df["_sum"] <= mean,
        (df["_sum"] > mean) & (df["_sum"] <= mean + std),
        (df["_sum"] > mean + std) & (df["_sum"] <= mean + 2 * std),
        (df["_sum"] > mean + 2 * std) & (df["_sum"] <= mean + 3 * std),
        df["_sum"] > mean + 3 * std,
    ]
    df["exposure"] = np.select(conditions, classes)
    return df


def main():
    cfg = load_config("exposure_config")

    exposure_vars = cfg["inputs"]["variables"]
    classes       = cfg["classification"]["classes"]
    class_col     = cfg["output"]["class_column"]
    time_col      = cfg["columns"]["time_column"]
    object_id_col = cfg["columns"]["object_id_column"]
    data_path     = os.path.join(_RISKMODEL_DIR, cfg["paths"]["data_folder"])

    master_variables = pd.read_csv(os.path.join(data_path, cfg["paths"]["input_file"]))

    results = []
    for month in tqdm(master_variables[time_col].unique()):
        month_data = master_variables[
            master_variables[time_col] == month
        ][exposure_vars + [time_col, object_id_col]].copy()
        results.append(calculate_exposure_scores(month_data, exposure_vars, classes))

    exposure         = pd.concat(results)
    master_variables = master_variables.merge(
        exposure[[time_col, object_id_col, class_col]],
        on=[time_col, object_id_col],
    )

    master_variables.to_csv(os.path.join(data_path, cfg["output"]["file"]), index=False)
    print("Results saved successfully!")


if __name__ == "__main__":
    main()
