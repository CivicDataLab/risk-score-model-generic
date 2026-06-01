from disaster_risk_score_model.common import (
    EXPOSURE_COL,
    classify_std_intervals,
    load_master,
    merge_and_save,
    score_by_month,
)
from disaster_risk_score_model.config import load_config


def main(config_dir=None, data_dir=None, input_file=None):
    cfg = load_config("exposure", config_dir=config_dir)

    value_vars = cfg["inputs"]["variables"]
    classes = cfg["classification"]["classes"]
    class_col = EXPOSURE_COL
    time_col = cfg["columns"]["time_column"]
    object_id_col = cfg["columns"]["object_id_column"]

    master, data_path = load_master(data_dir, input_file)
    scored = score_by_month(
        master,
        value_vars,
        time_col,
        object_id_col,
        lambda d: classify_std_intervals(d, value_vars, classes, class_col),
    )
    merge_and_save(
        master,
        scored,
        [time_col, object_id_col],
        [class_col],
        data_path / cfg["output"]["file"],
    )
    print("Results saved successfully!")
