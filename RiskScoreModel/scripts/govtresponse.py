import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm 
import os
import warnings

from config import govtresponse_config as cfg

# Suppress all warnings
warnings.filterwarnings("ignore")

master_variables = pd.read_csv(os.path.join(os.getcwd(), cfg.DATA_FOLDER, cfg.INPUT_FILE))


def get_financial_year(timeperiod):
    if int(timeperiod.split('_')[1]) >= 4:
        return str(int(timeperiod.split('_')[0]))+'-'+str(int(timeperiod.split('_')[0])+1)
    else:
        return str(int(timeperiod.split('_')[0]) - 1)+'-'+str(int(timeperiod.split('_')[0]))
    
# Apply the function to create the 'FinancialYear' column
master_variables[cfg.FINANCIAL_YEAR_COLUMN] = master_variables[cfg.TIME_COLUMN].apply(lambda x: get_financial_year(x))

#INPUT VARS
government_response_vars = cfg.GOVT_RESPONSE_VARS

# Find cumsum in each FY of the government response vars
for var in government_response_vars:
    master_variables[var]=master_variables.groupby([cfg.OBJECT_ID_COLUMN, cfg.FINANCIAL_YEAR_COLUMN])[var].cumsum()


govtresponse_df = master_variables[government_response_vars + [cfg.TIME_COLUMN, cfg.OBJECT_ID_COLUMN]]


govtresponse_df_months = []
for month in tqdm(govtresponse_df.timeperiod.unique()):
    govtresponse_df_month = govtresponse_df[govtresponse_df.timeperiod == month]
    # Initialize MinMaxScaler
    scaler = MinMaxScaler()
    # Fit scaler to the data and transform it
    govtresponse_df_month[government_response_vars] = scaler.fit_transform(govtresponse_df_month[government_response_vars])
    
    # Sum scaled exposure vars
    govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN] = govtresponse_df_month[government_response_vars].sum(axis=1)
    
    # Calculate mean and standard deviation
    mean = govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN].mean()
    std = govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN].std()
    
    # Define the conditions for each category
    conditions = [
        (govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN] <= mean),
        (govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN] > mean) & (govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN] <= mean + std),
        (govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN] > mean + std) & (govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN] <= mean + 2 * std),
        (govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN] > mean + 2 * std) & (govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN] <= mean + 3 * std),
        (govtresponse_df_month[cfg.GOVT_RESPONSE_SUM_COLUMN] > mean + 3 * std)
    ]
    
    
    # Create the new column based on the conditions
    govtresponse_df_month[cfg.GOVT_RESPONSE_CLASS_COLUMN] = np.select(conditions, cfg.GOVT_RESPONSE_CLASSES)

    govtresponse_df_months.append(govtresponse_df_month)

govtresponse = pd.concat(govtresponse_df_months)
master_variables = master_variables.merge(govtresponse[[cfg.TIME_COLUMN, cfg.OBJECT_ID_COLUMN, cfg.GOVT_RESPONSE_CLASS_COLUMN]],
                       on = [cfg.TIME_COLUMN, cfg.OBJECT_ID_COLUMN])

master_variables.to_csv(
    os.path.join(os.getcwd(), cfg.DATA_FOLDER, cfg.OUTPUT_FILE),
    index=False
)