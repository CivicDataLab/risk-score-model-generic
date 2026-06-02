from disaster_risk_score_model.common import (
    FINANCIAL_YEAR_COL,
    GOVTRESPONSE_COL,
    TIME_COLUMN,
    UNIT_ID_COLUMN,
    classify_std_intervals,
    load_master,
    merge_and_save,
    score_by_month,
)
from disaster_risk_score_model.config import load_config


def get_financial_year(time_period, start_month):
    year = int(time_period.split("-")[0])
    month = int(time_period.split("-")[1])
    if month >= start_month:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"


def main(config_dir=None, data_dir=None, input_file=None):
    cfg = load_config("govtresponse", config_dir=config_dir)

    value_vars = cfg["inputs"]["variables"]
    start_month = cfg["fiscal_year"]["start_month"]
    classes = cfg["classification"]["classes"]
    class_col = GOVTRESPONSE_COL
    fy_col = FINANCIAL_YEAR_COL
    time_col = TIME_COLUMN
    object_id_col = UNIT_ID_COLUMN

    master, data_path = load_master(data_dir, input_file)

    master[fy_col] = master[time_col].apply(lambda x: get_financial_year(x, start_month))

    # Accumulate spending within each fiscal year before scoring.
    for var in value_vars:
        master[var] = master.groupby([object_id_col, fy_col])[var].cumsum()

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
