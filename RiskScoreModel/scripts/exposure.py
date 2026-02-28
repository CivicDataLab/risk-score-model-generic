import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm 
import os
import warnings

from config import exposure_config as cfg

# Suppress all warnings
warnings.filterwarnings("ignore")

master_variables = pd.read_csv(os.path.join(os.getcwd(), cfg.DATA_FOLDER, cfg.INPUT_FILE))


base_path = os.path.join(os.getcwd(),
        #cfg.BASE_FOLDER,
        cfg.DATA_FOLDER
    )

exposure_vars = cfg.EXPOSURE_VARS

exposure_df = master_variables[exposure_vars + [cfg.TIME_COLUMN, cfg.OBJECT_ID_COLUMN]]

exposure_df_months = []
for month in tqdm(exposure_df.timeperiod.unique()):
    exposure_df_month = exposure_df[exposure_df.timeperiod == month]
    # Initialize MinMaxScaler
    scaler = MinMaxScaler()
    # Fit scaler to the data and transform it
    exposure_df_month[exposure_vars] = scaler.fit_transform(exposure_df_month[exposure_vars])
    
    # Sum scaled exposure vars
    
    exposure_df_month[cfg.EXPOSURE_SUM_COLUMN] = exposure_df_month[exposure_vars].sum(axis=1)
    
    # Calculate mean and standard deviation
    mean = exposure_df_month[cfg.EXPOSURE_SUM_COLUMN].mean()
    std = exposure_df_month[cfg.EXPOSURE_SUM_COLUMN].std()
    
    # Define the conditions for each category
    conditions = [
        (exposure_df_month[cfg.EXPOSURE_SUM_COLUMN] <= mean),
        (exposure_df_month[cfg.EXPOSURE_SUM_COLUMN] > mean) & (exposure_df_month[cfg.EXPOSURE_SUM_COLUMN] <= mean + std),
        (exposure_df_month[cfg.EXPOSURE_SUM_COLUMN] > mean + std) & (exposure_df_month[cfg.EXPOSURE_SUM_COLUMN] <= mean + 2 * std),
        (exposure_df_month[cfg.EXPOSURE_SUM_COLUMN] > mean + 2 * std) & (exposure_df_month[cfg.EXPOSURE_SUM_COLUMN] <= mean + 3 * std),
        (exposure_df_month[cfg.EXPOSURE_SUM_COLUMN] > mean + 3 * std)
    ]
    
    # Define the corresponding categories
    #categories = ['very low', 'low', 'medium', 'high', 'very high']
    categories = [1, 2, 3, 4, 5]
    
    # Create the new column based on the conditions
    exposure_df_month[cfg.EXPOSURE_CLASS_COLUMN] = np.select(conditions, categories)#, default='outlier')

    exposure_df_months.append(exposure_df_month)

exposure = pd.concat(exposure_df_months)

master_variables = master_variables.merge(exposure[[cfg.TIME_COLUMN, cfg.OBJECT_ID_COLUMN, cfg.EXPOSURE_CLASS_COLUMN]],
                       on = [cfg.TIME_COLUMN, cfg.OBJECT_ID_COLUMN])

master_variables.to_csv(
    os.path.join(os.getcwd(), cfg.DATA_FOLDER, cfg.OUTPUT_FILE),
    index=False
)