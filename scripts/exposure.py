import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from config.loader import load_config
from scripts.common import (
    EXPOSURE_COL,
    classify_std_intervals,
    load_master,
    merge_and_save,
    score_by_month,
)


def main():
    cfg = load_config("exposure_config")

    value_vars = cfg["inputs"]["variables"]
    classes = cfg["classification"]["classes"]
    class_col = EXPOSURE_COL
    time_col = cfg["columns"]["time_column"]
    object_id_col = cfg["columns"]["object_id_column"]

    master, data_path = load_master(cfg)
    scored = score_by_month(
        master, value_vars, time_col, object_id_col,
        lambda d: classify_std_intervals(d, value_vars, classes, class_col),
    )
    merge_and_save(
        master, scored, [time_col, object_id_col], [class_col],
        os.path.join(data_path, cfg["output"]["file"]),
    )
    print("Results saved successfully!")


if __name__ == "__main__":
    main()
