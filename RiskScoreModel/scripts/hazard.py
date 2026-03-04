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