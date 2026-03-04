import pandas as pd
import numpy as np
from tqdm import tqdm 
import os
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

from config import hazard_config as cfg

warnings.filterwarnings("ignore")

def calculate_hazard_scores(df, hazard_vars):
    """
    Calculate hazard scores using a single classification step.
    
    Args:
        df: DataFrame containing hazard variables
        hazard_vars: List of column names for hazard variables
        
    Returns:
        DataFrame with flood hazard classifications
    """
    # Log transform and standardize variables
    transformed_data = pd.DataFrame()
    for var in hazard_vars:
        transformed_data[var] = np.log1p(df[var])
        transformed_data[var] = (transformed_data[var] - transformed_data[var].mean()) / transformed_data[var].std()
    
    # Calculate composite score
    df[cfg.HAZARD_FLOAT_COLUMN] = transformed_data[hazard_vars].mean(axis=1)
    
    # Apply final classification
    thresholds = [
    df[cfg.HAZARD_FLOAT_COLUMN].quantile(q)
    for q in cfg.QUANTILE_THRESHOLDS
    ]
    
    conditions = [df[cfg.HAZARD_FLOAT_COLUMN] <= thresholds[0]]
    for i in range(len(thresholds) - 1):
        conditions.append(
            (df[cfg.HAZARD_FLOAT_COLUMN] > thresholds[i]) & 
            (df[cfg.HAZARD_FLOAT_COLUMN] <= thresholds[i + 1])
        )
    conditions.append(df[cfg.HAZARD_FLOAT_COLUMN] > thresholds[-1])
    
    df[cfg.HAZARD_CLASS_COLUMN] = np.select(conditions, cfg.HAZARD_CLASSES, default=1)
    
    return df[
    [
        cfg.TIME_COLUMN,
        cfg.OBJECT_ID_COLUMN,
        cfg.HAZARD_CLASS_COLUMN,
        cfg.HAZARD_FLOAT_COLUMN
    ]
]

def plot_hazard_distribution(df, output_path=None):
    """
    Create visualizations of the hazard distribution.
    
    Args:
        df: DataFrame containing hazard classifications
        output_path: Optional path to save the plots
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Bar plot
    sns.countplot(data=df, x=cfg.HAZARD_CLASS_COLUMN, ax=ax1, color='steelblue')
    ax1.set_title('Distribution of Flood Hazard Classes', pad=15)
    ax1.set_xlabel('Hazard Class')
    ax1.set_ylabel('Count')
    
    # Add count labels
    for p in ax1.patches:
        ax1.annotate(f'{int(p.get_height()):,}', 
                    (p.get_x() + p.get_width()/2., p.get_height()),
                    ha='center', va='bottom', fontsize=10)
    
    # Box plot
    sns.boxplot(data=df, x=cfg.HAZARD_CLASS_COLUMN, y=cfg.HAZARD_FLOAT_COLUMN, ax=ax2, color='lightblue')
    ax2.set_title('Distribution of Float Values by Hazard Class', pad=15)
    ax2.set_xlabel('Hazard Class')
    ax2.set_ylabel('Standardized Hazard Score')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\nPlot saved to: {output_path}")
    
    plt.show()

def validate_hazard_distribution(df):
    """
    Validate the hazard distribution and print statistics.
    
    Args:
        df: DataFrame containing hazard classifications
        
    Returns:
        bool: True if all validation checks pass
    """
    dist = df[cfg.HAZARD_CLASS_COLUMN].value_counts().sort_index()
    total = len(df)
    
    print("\nHazard Distribution Validation:")
    print("-" * 40)
    
    for class_num in range(1, 6):
        count = dist.get(class_num, 0)
        percentage = (count / total) * 100
        print(f"Class {class_num}: {count:,} ({percentage:.1f}%)")
    
    checks = {
        "All classes present": len(dist) == 5,
        "Class range valid": df[cfg.HAZARD_CLASS_COLUMN].between(1, 5).all(),
        "Decreasing trend": dist.iloc[0] > dist.iloc[-1],
        "No missing values": df[cfg.HAZARD_CLASS_COLUMN].notna().all()
    }
    
    print("\nValidation Checks:")
    print("-" * 40)
    for check, result in checks.items():
        print(f"{check}: {'✓' if result else '✗'}")
    
    return all(checks.values())


def main():
    # Configuration
    hazard_vars = cfg.HAZARD_VARS
    
    # Read data
    base_path = os.path.join(
    os.getcwd(),
    cfg.DATA_FOLDER
    )
    master_variables = pd.read_csv(os.path.join(base_path, cfg.INPUT_FILE))
    
    # Process each time period
    results = []
    for month in tqdm(master_variables[cfg.TIME_COLUMN].unique()):
        month_data = master_variables[
            master_variables[cfg.TIME_COLUMN] == month
        ][hazard_vars + [cfg.TIME_COLUMN, cfg.OBJECT_ID_COLUMN]].copy()
        
        results.append(calculate_hazard_scores(month_data, hazard_vars))
    
    # Combine and merge results
    hazard_scores = pd.concat(results)
    master_variables = master_variables.merge(
        hazard_scores, 
        on=[cfg.TIME_COLUMN, cfg.OBJECT_ID_COLUMN]
    )
        
    # Save results
    master_variables.to_csv(
        os.path.join(base_path, cfg.OUTPUT_FILE),
        index=False
    )
    print(f"\nResults saved successfully!")

if __name__ == "__main__":
    main()