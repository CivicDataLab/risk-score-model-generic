from config.base_config import *

# ==================================
# Government Response Configuration
# ==================================

# Input variables
GOVT_RESPONSE_VARS = [
    "total_tender_awarded_value",
    "SDRF_sanctions_awarded_value",
    "SDRF_tenders_awarded_value",
    #"total_expenditure_value",
    #"SOPD_tenders_awarded_value",
    #"RIDF_tenders_awarded_value",
    #"LTIF_tenders_awarded_value",
    #"CIDF_tenders_awarded_value",
    #"Preparedness Measures_tenders_awarded_value",
    #"Immediate Measures_tenders_awarded_value",
    #"Others_tenders_awarded_value",
    #'Repair and Restoration_tenders_awarded_value'
]

# Column names
FINANCIAL_YEAR_COLUMN = "financial_year"

GOVT_RESPONSE_SUM_COLUMN = "govt_response_sum"
GOVT_RESPONSE_CLASS_COLUMN = "government-response"

# Classification labels
# (Reverse scale because higher spending = better response = lower risk)
GOVT_RESPONSE_CLASSES = [5, 4, 3, 2, 1]

# Output file
OUTPUT_FILE = "factor_scores_l1_government-response.csv"