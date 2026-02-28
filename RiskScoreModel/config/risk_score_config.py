from config.base_config import *
from config.govtresponse_config import *
from config.exposure_config import *
from config.vulnerability_config import *
from config.hazard_config import *

# ==================================
# Final Risk Score Configuration
# ==================================

# TOPSIS weights
FLOOD_HAZARD_WEIGHT = 4
EXPOSURE_WEIGHT = 1
VULNERABILITY_WEIGHT = 2
RESPONSE_WEIGHT = 2

TOPSIS_WEIGHTS = [
    FLOOD_HAZARD_WEIGHT,
    EXPOSURE_WEIGHT,
    VULNERABILITY_WEIGHT,
    RESPONSE_WEIGHT
]

# Column headers
DISTRICT = "district"

# Risk factors used in TOPSIS
FACTORS = [
    "flood-hazard",
    "exposure",
    "vulnerability",
    "government-response"
]

# Additional columns to keep during merging
ADDITIONAL_COLUMNS = [
    "financial_year",
    "efficiency",
    "flood-hazard-float",
    "total_tenders_hist",
    "SDRF_sanctions_hist",
    "other_tenders_hist"
]

# Cumulative financial variables
CUMULATIVE_VARS = [
    "total_tender_awarded_value",
    "SDRF_sanctions_awarded_value",
    "SDRF_tenders_awarded_value",
    "Preparedness Measures_tenders_awarded_value",
    "Immediate Measures_tenders_awarded_value",
    "Others_tenders_awarded_value"
]

# TOPSIS output columns
TOPSIS_SCORE_COLUMN = "TOPSIS_Score"
RISK_SCORE_COLUMN = "risk-score"

# Risk score classes
RISK_CLASSES = [1, 2, 3, 4, 5]

# Factor score file pattern
FACTOR_SCORE_PATTERN = "factor_scores_l1*.csv"

# Output files
RISK_SCORE_FILE = "risk_score.csv"
FINAL_DISTRICT_FILE = "risk_score_final_district.csv"

# District assets
DISTRICT_OBJECT_FILE = "assets/district_objectid.csv"

# District grouping columns
DISTRICT_COLUMNS = ["district", "timeperiod"]

# Indicators
INDICATORS = ['total-tender-awarded-value',
    'sopd-tenders-awarded-value',
    'sdrf-sanctions-awarded-value',
    'sdrf-tenders-awarded-value',
    'ridf-tenders-awarded-value',
    'ltif-tenders-awarded-value',
    'cidf-tenders-awarded-value',
    'preparedness-measures-tenders-awarded-value',
    'immediate-measures-tenders-awarded-value',

    'others-tenders-awarded-value',
    'others-tenders-awarded-value-fy-cumsum',

    'total-tender-awarded-value-fy-cumsum',
    'sdrf-sanctions-awarded-value-fy-cumsum',
    'sdrf-tenders-awarded-value-fy-cumsum',
    'preparedness-measures-tenders-awarded-value-fy-cumsum',
    'immediate-measures-tenders-awarded-value-fy-cumsum',

    'total-expenditure-value',
    'immediate-measures-expenditure-value',
    'others-expenditure-value',
    'sdrf-expenditure-value',
    #'sopd-expenditure-value',
    'repair-and-restoration-expenditure-value',

    'total-animal-washed-away',
    'total-animal-affected',
    'total-house-fully-damaged',
    'embankments-affected',
    'roads',
    'bridge',
    'embankment-breached',
    'sum-population',
    'inundation-intensity-sum',
    'total-hhd',
    'human-live-lost',
    'sum-aged-population',
    'schools-count',
    'health-centres-count',
    'road-length',
    'rail-length',
    'rc-nosanitation-hhds-pct',
    'drainage-density',
    #'flood-hazard',
    'inundation-pct',
    'inundation-intensity-mean',
    'inundation-intensity-mean-nonzero',
    'avg-electricity',
    'rc-piped-hhds-pct',
    'mean-sex-ratio',
    'population-affected-total',
    'crop-area',
    'elevation-mean',
    'mean-ndvi',
    'mean-ndbi',
    'rc-area',
    #'are-new',
    'riverlevel-mean',
    'riverlevel-min',
    'riverlevel-max',
    'sum-young-population',
    'mean-cn',
    'slope-mean',
    'avg-tele',
    'distance-from-river',
    'water',
    'trees',
    'rangeland',
    'crops',
    'flooded-vegetation',
    'built-area',
    'bare-ground',
    'clouds',
    'net-sown-area-in-hac',
    #'road-count',
    'rail-count',
    'max-rain',
    'mean-rain',
    'sum-rain',
    'efficiency',
    'financial-year',
    'relief-camps',
    'relief-centers', 
    'relief-inmates',
    
    #'total-tenders-hist', 
    #"sdrf-sanctions-hist", 
    #"other-tenders-hist",    
    #'flood-hazard-float'

    'topsis-score'
    #'risk-score',
    #'exposure',
    #'vulnerability',
    #'government-response',
    ]

# Aggregation rules
AGGREGATION_RULES = {
    # Sum columns
    'total-tender-awarded-value': 'sum',
    'sopd-tenders-awarded-value': 'sum',
    'sdrf-sanctions-awarded-value': 'first',
    'sdrf-tenders-awarded-value': 'sum',
    'ridf-tenders-awarded-value': 'sum',
    'ltif-tenders-awarded-value': 'sum',
    'cidf-tenders-awarded-value': 'sum',
    'preparedness-measures-tenders-awarded-value': 'sum',
    'immediate-measures-tenders-awarded-value': 'sum',
    'others-tenders-awarded-value': 'sum',

    'others-tenders-awarded-value-fy-cumsum': 'sum',

    'total-tender-awarded-value-fy-cumsum': 'sum',
    'sdrf-sanctions-awarded-value-fy-cumsum': 'first',
    'sdrf-tenders-awarded-value-fy-cumsum': 'sum',
    'preparedness-measures-tenders-awarded-value-fy-cumsum': 'sum',
    'immediate-measures-tenders-awarded-value-fy-cumsum': 'sum',

    'total-expenditure-value': 'sum',
    'immediate-measures-expenditure-value': 'sum',
    'others-expenditure-value': 'sum',
    'sdrf-expenditure-value': 'sum',
    #'sopd-expenditure-value': 'sum',
    'repair-and-restoration-expenditure-value': 'sum',

    'total-animal-washed-away': 'sum',
    'total-animal-affected': 'sum',
    'total-house-fully-damaged': 'sum',
    'embankments-affected': 'sum',
    'roads': 'sum',
    'bridge': 'sum',
    'embankment-breached': 'sum',
    'sum-population': 'sum',
    'inundation-intensity-sum': 'sum',
    'total-hhd': 'sum',
    'human-live-lost': 'sum',
    'sum-aged-population': 'sum',
    'schools-count': 'sum',
    'health-centres-count': 'sum',
    'road-length': 'sum',
    'rail-length': 'sum',
    'sum-rain': 'sum',
    'rc-area':'sum',
    #'are-new':'sum',
    'sum-young-population':'sum',
    'net-sown-area-in-hac':'sum',
    #'road-count':'sum',
    'rail-count':'sum',
    'population-affected-total': 'sum',
    'crop-area': 'sum',
    'relief-camps':'sum',
    'relief-centers':'sum', 
    'relief-inmates':'sum',

    # Mean for percentage or density-based metrics
    'rc-nosanitation-hhds-pct': 'mean',
    'drainage-density': 'mean',
    #'flood-hazard': 'mean',
    'inundation-pct': 'mean',
    'inundation-intensity-mean-nonzero': 'mean',
    'inundation-intensity-mean': 'mean',
    'avg-electricity': 'mean',
    'rc-piped-hhds-pct': 'mean',
    'mean-sex-ratio': 'mean',
    'mean-rain':'mean',
    'elevation-mean':'mean',
    'mean-ndvi':'mean',
    'mean-ndbi':'mean',
    'riverlevel-mean':'mean',
    'mean-cn':'mean',
    'slope-mean':'mean',
    'avg-tele':'mean',
    'distance-from-river':'mean',
    'water':'mean',
    'trees':'mean',
    'rangeland':'mean',
    'crops':'mean',
    'flooded-vegetation':'mean',
    'built-area':'mean',
    'bare-ground':'mean',
    'clouds':'mean',
    'efficiency':'mean',
    #'total-tenders-hist':'mean', 
    #"sdrf-sanctions-hist":"mean", 
    #"other-tenders-hist":"mean",    
    #'flood-hazard-float':"mean",

    'topsis-score': 'mean',
    #'risk-score': 'mean',
    #'exposure': 'mean',
    #'vulnerability': 'mean',
    #'government-response': 'mean',

    # Max for hazard levels
    'max-rain':'max',
    'riverlevel-max':'max',
    'riverlevel-min':'min',
    'financial-year': 'first' 
}

# Rounding rules
ROUNDING_RULES = {
    'avg-tele': 1,  # Round column 'A' to 1 decimal place
    'avg-electricity': 1,

    'mean-sex-ratio': 2,  
    'inundation-intensity-mean-nonzero': 2,  
    'rc-piped-hhds-pct':2,
    'rc-nosanitation-hhds-pct':2,
    'inundation-intensity-sum':2,
    'max-rain':2,
    'mean-rain':2,
    'sum-rain':2,

    
    'sum-aged-population': 0,   # Round column 'C' to no decimal places
    'sum-young-population': 0,
    'sum-population':0,
    'rail-length':0,
    'road-length':0,
    'elevation-mean':0,
    'slope-mean':0,
    'crop-area':0,

}