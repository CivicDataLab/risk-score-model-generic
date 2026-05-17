# Getting Started — Adapting the Model to a New Geography

This guide walks through everything required to run the risk score model for a new geography, from collecting input data to producing the final composite risk score.

For methodology detail on any individual score, see the [document index](./README.md).

---

## Pipeline Overview

```mermaid
flowchart TD
    A([MASTER_VARIABLES.csv\nOne row per geographic unit per month]) --> B & C & D & E

    B[hazard.py] --> B1[factor_scores_l1_flood-hazard.csv]
    C[exposure.py] --> C1[factor_scores_l1_exposure.csv]
    D[vulnerability.py] --> D1[factor_scores_l1_vulnerability.csv]
    E[govtresponse.py] --> E1[factor_scores_l1_government-response.csv]

    B1 & C1 & D1 & E1 --> F[topis_riskscore_district.py]

    F --> G([risk_score_final_district.csv\nComposite risk score — block and district level])
```

The four factor scripts are independent of each other and can run in any order. The TOPSIS script must run after all four have completed.

---

## Step 1 — Collect Your Input Data

All scripts read from a single master CSV file:

**`RiskScoreModel/data/MASTER_VARIABLES.csv`**

One row per geographic unit per month. The following columns are required by every script:

| Column | Type | Description |
|--------|------|-------------|
| `object_id` | Integer | Unique identifier for each geographic unit |
| `timeperiod` | String (`YYYY_MM`) | Month identifier, e.g. `2022_07` |
| `district` | String | Parent district name for each unit |

In addition, each factor score requires its own input variables. The table below shows the default variables and the minimum viable set for each factor:

### Hazard

| Column | Description | Min. requirement |
|--------|-------------|-----------------|
| `inundation_intensity_mean_nonzero` | Mean flood inundation intensity | Any measure of flood water extent or depth |
| `inundation_intensity_sum` | Cumulative inundation intensity | Any cumulative flood exposure measure |
| `drainage_density` | Stream length per unit area | km/km² or equivalent |
| `mean_rain` | Mean rainfall in the unit | mm or consistent unit |
| `max_rain` | Maximum rainfall pixel value | mm or consistent unit |

**Minimum viable:** any 2 or more of the above. See [score_hazard.md](./score_hazard.md) for alternative data sources.

### Exposure

| Column | Description | Min. requirement |
|--------|-------------|-----------------|
| `sum_population` | Total estimated population | Any population count |
| `total_hhd` | Total number of households | Any household count |

**Minimum viable:** 1 variable. See [score_exposure.md](./score_exposure.md) for alternative data sources.

### Vulnerability

Requires two groups of variables:

**Condition inputs** (structural characteristics):

| Column | Description |
|--------|-------------|
| `mean_sex_ratio` | Females per 1,000 males |
| `schools_count` | Schools per km² |
| `health_centres_count` | Health centres per km² |
| `rail_length` | Rail track length per km² |
| `road_length` | Road length per km² |
| `net_sown_area_in_hac` | Agricultural sown area |
| `avg_electricity` | Electricity access score (0–1) |
| `rc_piped_hhds_pct` | Percentage of households with piped water |
| `rc_nosanitation_hhds_pct` | Percentage of households without sanitation |
| `sum_aged_population` | Elderly population per km² |
| `Embankment breached` | Flood protection failures per km² |

**Damage outputs** (observed flood impacts):

| Column | Description |
|--------|-------------|
| `Human_Live_Lost` | Deaths per capita |
| `Population_affected_Total` | Affected population per capita |
| `Crop_Area` | Damaged crop area / total sown area |
| `Embankments affected` | Embankment damage per km² |
| `Roads` | Road damage per km² |
| `Bridge` | Bridge damage per km² |

> **If damage data is not available:** The DEA method used for vulnerability scoring requires observed damage data to function correctly. Without it, consider replacing the DEA with a simpler weighted index over the condition variables. See [score_vulnerability.md](./score_vulnerability.md) for detail.

See [score_vulnerability.md](./score_vulnerability.md) for alternative data sources.

### Government Response

| Column | Description | Min. requirement |
|--------|-------------|-----------------|
| `total_tender_awarded_value` | Total value of all flood-related contracts awarded | Any measure of total disaster-related procurement |
| `SDRF_sanctions_awarded_value` | Value of disaster fund sanctions | Disaster fund disbursements or equivalent |
| `SDRF_tenders_awarded_value` | Value of scheme-specific contracts | Optional; can be omitted |

**Minimum viable:** 1 variable representing total government flood expenditure. See [score_government_response.md](./score_government_response.md) for alternative data sources including OCDS-format procurement data.

### District ID Lookup

**`RiskScoreModel/assets/district_objectid.csv`**

Maps district names to the platform's geographic IDs. Required by the TOPSIS script for district-level aggregation. Must contain:

| Column | Description |
|--------|-------------|
| `district` | District name matching the values in `MASTER_VARIABLES.csv` |
| `object_id` | Platform-level object ID for that district |

---

## Step 2 — Configure the Project

All configuration lives in TOML files under `RiskScoreModel/config/`. You do not need to edit any Python scripts to adapt the model — only the TOML files.

### `RiskScoreModel/config/base_config.toml`

Always review this first. It sets the shared paths and column names used by every script.

| Setting | Default | Change if... |
|---------|---------|-------------|
| `paths.data_folder` | `data` | Your data folder is named differently |
| `paths.input_file` | `MASTER_VARIABLES.csv` | Your input file has a different name |
| `columns.time_column` | `timeperiod` | Your time column has a different name |
| `columns.object_id_column` | `object_id` | Your geographic ID column is named differently |

### `RiskScoreModel/config/hazard_config.toml`

| Setting | Default | Change if... |
|---------|---------|-------------|
| `inputs.variables` | 5 rainfall/inundation columns | You have different or fewer hazard variables |
| `classification.quantile_thresholds` | `[0.35, 0.60, 0.80, 0.95]` | You want different classification boundaries |
| `classification.classes` | `[1, 2, 3, 4, 5]` | You want a different number of risk classes |

### `RiskScoreModel/config/exposure_config.toml`

| Setting | Default | Change if... |
|---------|---------|-------------|
| `inputs.variables` | `sum_population`, `total_hhd` | You have different population/household columns (min: 1) |
| `classification.classes` | `[1, 2, 3, 4, 5]` | You want different class labels |

### `RiskScoreModel/config/vulnerability_config.toml`

| Setting | Default | Change if... |
|---------|---------|-------------|
| `inputs.condition_vars` | 11 infrastructure/demographic columns | You have different structural condition variables |
| `inputs.damage_vars` | 6 flood damage columns | You have different damage variables (or none — see note below) |
| `inputs.inverted_inputs` | 6 resilience variables | You change condition_vars — update which variables are inverted |
| `inputs.neg_inputs` | 3 negative-polarity variables | You change condition_vars |
| `normalisation.per_capita` | 4 variables ÷ population | Update denominators to match your data |
| `normalisation.per_area` | 11 variables ÷ area | Update denominators to match your data |
| `classification.n_classes` | `5` | You want a different number of vulnerability classes |
| `classification.damage_threshold` | `0.0001` | You want to change the damage significance threshold |

> **If damage data is not available:** The DEA method requires observed damage data. Without it, consider replacing the DEA with a simpler weighted index over `inputs.condition_vars` only.

### `RiskScoreModel/config/govtresponse_config.toml`

| Setting | Default | Change if... |
|---------|---------|-------------|
| `inputs.variables` | 3 tender/SDRF columns | You have different expenditure columns (min: 1) |
| `fiscal_year.start_month` | `4` (April) | Your geography uses a different fiscal year calendar |

### `RiskScoreModel/config/topsis_config.toml`

| Setting | Default | Change if... |
|---------|---------|-------------|
| `weights.*` | hazard=4, exposure=1, vulnerability=2, response=2 | You want to re-weight factors based on local context or policy |
| `classification.n_bins` | `5` | You want a different number of output risk classes |
| `paths.district_lookup_file` | `assets/district_objectid.csv` | You replace the district ID lookup |
| `[indicators]` | 70+ India-specific columns with aggregation rules | Remove rows for columns absent in your data |
| `[rounding]` | Per-column decimal precision | You want different output rounding |

---

## Step 3 — Run the Scripts

All scripts should be run from the repository root. The four factor scripts are independent and can run in any order (or in parallel):

```bash
python RiskScoreModel/scripts/hazard.py
python RiskScoreModel/scripts/exposure.py
python RiskScoreModel/scripts/vulnerability.py
python RiskScoreModel/scripts/govtresponse.py
```

Once all four have completed, run the TOPSIS aggregation:

```bash
python RiskScoreModel/scripts/topis_riskscore_district.py
```

---

## Step 4 — Validate Your Outputs

After running all scripts, the following files should be present in `RiskScoreModel/data/`:

| File | What to check |
|------|--------------|
| `factor_scores_l1_flood-hazard.csv` | `flood-hazard` column present; values in range 1–5; all 5 classes represented |
| `factor_scores_l1_exposure.csv` | `exposure` column present; values in range 1–5 |
| `factor_scores_l1_vulnerability.csv` | `vulnerability` column present; values in range 1–5; `efficiency` column in range 0–1 |
| `factor_scores_l1_government-response.csv` | `government-response` column present; values in range 1–5 |
| `risk_score.csv` | `risk-score` and `TOPSIS_Score` columns present; no missing values |
| `risk_score_final_district.csv` | Contains both block-level and district-level rows; district rows have matching `district` and `block_name` fields |

The hazard script also saves a diagnostic plot (`data/hazard_distribution.png`) showing the class distribution — a roughly decreasing distribution (more low-risk units than high-risk) is expected.

If any factor score shows only 1–2 classes represented, it usually indicates that the input variable has very low variance for that geography or time period. Review the input data distribution for that factor.
