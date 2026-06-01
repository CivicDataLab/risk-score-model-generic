import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from config.loader import load_config
from scripts.common import load_master, merge_and_save, score_by_month


def calculate_hazard_scores(df, cfg):
    hazard_vars = cfg["inputs"]["variables"]
    float_col = cfg["output"]["float_column"]
    class_col = cfg["output"]["class_column"]

    transformed = pd.DataFrame()
    for var in hazard_vars:
        transformed[var] = np.log1p(df[var])
        mean = transformed[var].mean()
        std = transformed[var].std()
        transformed[var] = (transformed[var] - mean) / std

    df[float_col] = transformed[hazard_vars].mean(axis=1)

    thresholds = [df[float_col].quantile(q) for q in cfg["classification"]["quantile_thresholds"]]

    conditions = [df[float_col] <= thresholds[0]]
    for i in range(len(thresholds) - 1):
        conditions.append(
            (df[float_col] > thresholds[i]) & (df[float_col] <= thresholds[i + 1])
        )
    conditions.append(df[float_col] > thresholds[-1])

    df[class_col] = np.select(conditions, cfg["classification"]["classes"], default=1)

    time_col = cfg["columns"]["time_column"]
    object_id_col = cfg["columns"]["object_id_column"]
    return df[[time_col, object_id_col, class_col, float_col]]


def plot_hazard_distribution(df, cfg, output_path=None):
    float_col = cfg["output"]["float_column"]
    class_col = cfg["output"]["class_column"]
    figsize = cfg["plot"]["figsize"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    sns.countplot(data=df, x=class_col, ax=ax1, color="steelblue")
    ax1.set_title("Distribution of Flood Hazard Classes", pad=15)
    ax1.set_xlabel("Hazard Class")
    ax1.set_ylabel("Count")
    for p in ax1.patches:
        ax1.annotate(
            f"{int(p.get_height()):,}",
            (p.get_x() + p.get_width() / 2.0, p.get_height()),
            ha="center", va="bottom", fontsize=10,
        )

    sns.boxplot(data=df, x=class_col, y=float_col, ax=ax2, color="lightblue")
    ax2.set_title("Distribution of Float Values by Hazard Class", pad=15)
    ax2.set_xlabel("Hazard Class")
    ax2.set_ylabel("Standardized Hazard Score")

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=cfg["plot"]["dpi"], bbox_inches="tight")
        print(f"\nPlot saved to: {output_path}")
    plt.show()


def validate_hazard_distribution(df, cfg):
    class_col = cfg["output"]["class_column"]
    dist = df[class_col].value_counts().sort_index()
    total = len(df)

    print("\nHazard Distribution Validation:")
    print("-" * 40)
    for class_num in range(1, 6):
        count = dist.get(class_num, 0)
        print(f"Class {class_num}: {count:,} ({count / total * 100:.1f}%)")

    checks = {
        "All classes present": len(dist) == 5,
        "Class range valid": df[class_col].between(1, 5).all(),
        "Decreasing trend": dist.iloc[0] > dist.iloc[-1],
        "No missing values": df[class_col].notna().all(),
    }

    print("\nValidation Checks:")
    print("-" * 40)
    for check, result in checks.items():
        print(f"{check}: {'✓' if result else '✗'}")

    return all(checks.values())


def print_variable_statistics(df, hazard_vars):
    print("\nVariable Statistics:")
    print("-" * 40)
    for var in hazard_vars:
        stats = df[var].describe()
        print(f"\n{var}:")
        print(f"  Mean: {stats['mean']:.2f}  Std: {stats['std']:.2f}")
        print(f"  Min:  {stats['min']:.2f}  Max: {stats['max']:.2f}")
        print(f"  Skew: {df[var].skew():.2f}")


def main():
    cfg = load_config("hazard_config")

    hazard_vars = cfg["inputs"]["variables"]
    float_col = cfg["output"]["float_column"]
    class_col = cfg["output"]["class_column"]
    time_col = cfg["columns"]["time_column"]
    object_id_col = cfg["columns"]["object_id_column"]

    master, data_path = load_master(cfg)

    print_variable_statistics(master, hazard_vars)

    scored = score_by_month(
        master, hazard_vars, time_col, object_id_col,
        lambda d: calculate_hazard_scores(d, cfg),
    )
    master = merge_and_save(
        master, scored, [time_col, object_id_col], [class_col, float_col],
        os.path.join(data_path, cfg["output"]["file"]),
    )

    is_valid = validate_hazard_distribution(master, cfg)
    if is_valid:
        print("\nHazard distribution passes all validation checks!")
    else:
        print("\nWarning: Some validation checks failed. Please review the distribution.")

    plot_hazard_distribution(
        master, cfg,
        os.path.join(data_path, cfg["output"]["plot_file"]),
    )

    print("\nResults saved successfully!")


if __name__ == "__main__":
    main()
