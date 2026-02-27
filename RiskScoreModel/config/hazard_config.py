from config.base_config import *

# Hazard Variables
HAZARD_VARS = [
    "inundation_intensity_mean_nonzero",
    "inundation_intensity_sum",
    "drainage_density",
    "mean_rain",
    "max_rain",
]

# Thresholds
QUANTILE_THRESHOLDS = [0.35, 0.60, 0.80, 0.95]

# Hazard Classes
HAZARD_CLASSES = [1, 2, 3, 4, 5]

# Column Names
HAZARD_FLOAT_COLUMN = "flood-hazard-float"
HAZARD_CLASS_COLUMN = "flood-hazard"

# Output
PLOT_FILE = "hazard_distribution.png"
OUTPUT_FILE = "factor_scores_l1_flood-hazard.csv"

# Plot Settings
PLOT_FIGSIZE = (15, 6)
PLOT_DPI = 300