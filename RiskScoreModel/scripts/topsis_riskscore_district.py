from scripts.data_models import topsis
import pandas as pd
import numpy as np 
import os
import glob

from config import risk_score_config as cfg

weights = cfg.TOPSIS_WEIGHTS

## MASTER DATA WITH FACTOR SCORES
print(os.getcwd())

## INPUT: FACTOR SCORES CSV
factor_scores_dfs = glob.glob(
    os.path.join(os.getcwd(), cfg.DATA_FOLDER, cfg.FACTOR_SCORE_PATTERN)
)

# Select only the columns that exist in both the DataFrame and the list
factors = cfg.FACTORS
additional_columns = cfg.ADDITIONAL_COLUMNS

merged_df = pd.read_csv(factor_scores_dfs[0])
print(merged_df.shape)

# Merge successive DataFrames in the list
for df in factor_scores_dfs[1:]:
    df = pd.read_csv(df)
    print(df.shape)
    selected_columns = [col for col in factors if col in df.columns]
    selected_additional_columns = [col for col in additional_columns if col in df.columns]

    # Create a new DataFrame containing only the selected columns
    df = df[selected_columns + [cfg.OBJECT_ID_COLUMN, cfg.TIME_COLUMN] + selected_additional_columns]
    
    #merged_df = pd.merge(merged_df, df, on=[cfg.OBJECT_ID_COLUMN, cfg.TIME_COLUMN], how='inner')
    merged_df = pd.merge(
        merged_df, df, on=[cfg.OBJECT_ID_COLUMN, cfg.TIME_COLUMN], how='inner', suffixes=('', '_drop')
    )

    # Drop the duplicate columns after the merge
    merged_df = merged_df.loc[:, ~merged_df.columns.str.endswith('_drop')]

#df = pd.read_csv(os.getcwd()+'/RiskScoreModel/data/factor_scores.csv')
df_months = []

# Ensure sorting for proper cumulative sum
merged_df.sort_values(by=[cfg.OBJECT_ID_COLUMN, cfg.FINANCIAL_YEAR_COLUMN, cfg.TIME_COLUMN], inplace=True)

# Define indicators that need cumulative sums
cumulative_vars = cfg.CUMULATIVE_VARS

for var in cumulative_vars:
    cum_var_name = var + "_fy_cumsum"
    merged_df[cum_var_name] = merged_df.groupby([cfg.OBJECT_ID_COLUMN, cfg.FINANCIAL_YEAR_COLUMN])[var].cumsum()

for month in merged_df.timeperiod.unique():

    df_month = merged_df[merged_df.timeperiod==month]

    evaluation_matrix = np.array(df_month[factors].values)

    criterias = [True] * len(factors)

    # All variables - more is more risk; 'government-response' is in reverse

    t = topsis.Topsis(evaluation_matrix, weights, criterias)
    t.calc()
    df_month[cfg.TOPSIS_SCORE_COLUMN] = t.worst_similarity
    df_month = df_month.sort_values(by=cfg.TOPSIS_SCORE_COLUMN, ascending=False)
    
    compositescorelabels = cfg.RISK_CLASSES
    compscore = pd.cut(df_month[cfg.TOPSIS_SCORE_COLUMN],bins = 5,precision = 0,labels = compositescorelabels )
    df_month[cfg.RISK_SCORE_COLUMN] = compscore

    df_months.append(df_month)

topsis = pd.concat(df_months)

print(topsis.shape)
topsis.columns = [col.lower().replace('_', '-').replace(' ', '-') for col in topsis.columns]
print(topsis.columns)

topsis.to_csv(
    os.path.join(os.getcwd(), cfg.DATA_FOLDER, cfg.RISK_SCORE_FILE),
    index=False
)
## DISTRICT LEVEL SCORES
dist_ids = pd.read_csv(
    os.path.join(os.getcwd(), cfg.DISTRICT_OBJECT_FILE)
)

compositescorelabels = cfg.RISK_CLASSES

dist_vul = topsis.groupby([cfg.DISTRICT,cfg.TIME_COLUMN])[cfg.VULNERABILITY_CLASS_COLUMN].mean().reset_index()
compscore = pd.cut(dist_vul[cfg.VULNERABILITY_CLASS_COLUMN],bins = 5,precision = 0,labels = compositescorelabels )
dist_vul[cfg.VULNERABILITY_CLASS_COLUMN] = compscore
dist_vul = dist_vul.merge(dist_ids, on=cfg.DISTRICT)

dist_exp = topsis.groupby([cfg.DISTRICT,cfg.TIME_COLUMN])[cfg.EXPOSURE_CLASS_COLUMN].mean().reset_index()
compscore = pd.cut(dist_exp[cfg.EXPOSURE_CLASS_COLUMN],bins = 5,precision = 0,labels = compositescorelabels )
dist_exp[cfg.EXPOSURE_CLASS_COLUMN] = compscore
dist_exp = dist_exp.merge(dist_ids, on=cfg.DISTRICT)

dist_govt = topsis.groupby([cfg.DISTRICT,cfg.TIME_COLUMN])[cfg.GOVT_RESPONSE_CLASS_COLUMN].mean().reset_index()
compscore = pd.cut(dist_govt[cfg.GOVT_RESPONSE_CLASS_COLUMN],bins = 5,precision = 0,labels = compositescorelabels )
dist_govt[cfg.GOVT_RESPONSE_CLASS_COLUMN] = compscore
dist_govt = dist_govt.merge(dist_ids, on=cfg.DISTRICT)

dist_haz = topsis.groupby([cfg.DISTRICT,cfg.TIME_COLUMN])[cfg.HAZARD_CLASS_COLUMN].mean().reset_index()
compscore = pd.cut(dist_haz[cfg.HAZARD_CLASS_COLUMN],bins = 5,precision = 0,labels = compositescorelabels )
dist_haz[cfg.HAZARD_CLASS_COLUMN] = compscore
dist_haz = dist_haz.merge(dist_ids, on=cfg.DISTRICT)

topsis[cfg.RISK_SCORE_COLUMN] = topsis[cfg.RISK_SCORE_COLUMN].astype(int)
dist_risk = topsis.groupby([cfg.DISTRICT,cfg.TIME_COLUMN])[cfg.RISK_SCORE_COLUMN].mean().reset_index()
compscore = pd.cut(dist_risk[cfg.RISK_SCORE_COLUMN],bins = 5,precision = 0,labels = compositescorelabels )
dist_risk[cfg.RISK_SCORE_COLUMN] = compscore
dist_risk = dist_risk.merge(dist_ids, on=cfg.DISTRICT)


indicators = cfg.INDICATORS
aggregation_rules = cfg.AGGREGATION_RULES
rounding_rules = cfg.ROUNDING_RULES

dist_indicators = topsis.groupby([cfg.DISTRICT, cfg.TIME_COLUMN]).agg(aggregation_rules).reset_index()

def apply_rounding_rules(df, rounding_rules):
    """
    Apply multiple rounding rules to a DataFrame.

    Parameters:
    df (pd.DataFrame): The input DataFrame.
    rounding_rules (dict): A dictionary where keys are column names and values are the number of decimals to round to.

    Returns:
    pd.DataFrame: The DataFrame with applied rounding rules.
    """
    for column, decimals in rounding_rules.items():
        if column in df.columns:
            df[column] = df[column].round(decimals)
        else:
            print(f"Column {column} does not exist in DataFrame.")
    return df

'''

dist = pd.concat([dist_indicators, 
                  dist_vul['vulnerability'],
                  dist_exp['exposure'], 
                  dist_govt['government-response'], 
                  dist_haz['flood-hazard'], 
                  dist_risk['risk-score']], 
                  axis=1)
'''
dist = pd.concat([dist_vul.set_index([cfg.DISTRICT, cfg.TIME_COLUMN]),
                  dist_exp.set_index([cfg.DISTRICT, cfg.TIME_COLUMN])[cfg.EXPOSURE_CLASS_COLUMN],
                  dist_govt.set_index([cfg.DISTRICT, cfg.TIME_COLUMN])[cfg.GOVT_RESPONSE_CLASS_COLUMN],
                  dist_haz.set_index([cfg.DISTRICT, cfg.TIME_COLUMN])[cfg.HAZARD_CLASS_COLUMN],
                  dist_risk.set_index([cfg.DISTRICT, cfg.TIME_COLUMN])[cfg.RISK_SCORE_COLUMN],
                  dist_indicators.set_index([cfg.DISTRICT, cfg.TIME_COLUMN])[indicators]],
                  axis=1).reset_index()
#print(dist.columns)
#print(topsis.columns)


final = pd.concat([topsis, dist], ignore_index=True)

# Apply rounding rules
final = apply_rounding_rules(final, rounding_rules)
final['inundation-pct'] = final['inundation-pct']*100


#final = pd.concat([topsis.set_index(['object-id', cfg.TIME_COLUMN]),
#                   dist.set_index(['object-id', cfg.TIME_COLUMN])], axis=1).reset_index()
final["total-infrastructure-damage"] =  final["total-house-fully-damaged"] + final["roads"] + final["bridge"]
final.rename(columns={'preparedness-measures-tenders-awarded-value': 'restoration-measures-tenders-awarded-value', 'mean-sexratio':'sexratio'}, inplace=True)

final.to_csv(
    os.path.join(os.getcwd(), cfg.DATA_FOLDER, cfg.FINAL_DISTRICT_FILE),
    index=False
)

#dist.rename(columns={'preparedness-measures-tenders-awarded-value': 'restoration-measures-tenders-awarded-value'}, inplace=True)
#dist.to_csv(os.getcwd()+r'/IDS-DRR-Assam/RiskScoreModel/data/risk_score_final_dist.csv', index=False)

