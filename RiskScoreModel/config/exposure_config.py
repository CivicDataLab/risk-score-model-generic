from config.base_config import *

# ==============================
# Exposure Model Configuration
# ==============================

# Exposure variables
EXPOSURE_VARS = [
    "sum_population",
    "total_hhd"
]

# Column names
EXPOSURE_SCORE_COLUMN = "exposure_score"
EXPOSURE_CLASS_COLUMN = "exposure"

# Temporary column used during calculation
EXPOSURE_SUM_COLUMN = "sum"

# Classification labels
EXPOSURE_CLASSES = [1, 2, 3, 4, 5]

# Output file
OUTPUT_FILE = "factor_scores_l1_exposure.csv"