# IDS-DRR Risk Score Model — Methodology Documentation

This directory documents the **scoring methodology** for the IDS-DRR risk model. These files are intended for DPGA certification and for implementers who want to adapt the model to a new geography or data source.

The model takes a master dataset of spatial variables (one row per geographic unit per month) and produces a composite flood risk score using four factor scores combined via TOPSIS.

---

## Repository Context

```
risk-score-model-generic/
└── RiskScoreModel/
    ├── config/         ← configurable thresholds and variable lists
    ├── data/           ← MASTER_VARIABLES.csv input + output CSVs
    ├── scripts/        ← scoring computation scripts
    └── docs/           ← THIS DIRECTORY — methodology documentation
```

> **Source data documentation** (how raw datasets are ingested and transformed into `MASTER_VARIABLES.csv`) lives in the companion repository:
> `flood-data-ecosystem-generic/docs/`

---

## Full Pipeline Overview

```mermaid
flowchart TD
    A([MASTER_VARIABLES.csv\nOne row per geographic unit per month\n45+ variables]) --> B

    subgraph FactorScores["Factor Score Scripts"]
        B[hazard.py] --> B1[factor_scores_l1_flood-hazard.csv\nflood-hazard class 1–5]
        C[exposure.py] --> C1[factor_scores_l1_exposure.csv\nexposure class 1–5]
        D[vulnerability.py] --> D1[factor_scores_l1_vulnerability.csv\nvulnerability class 1–5]
        E[govtresponse.py] --> E1[factor_scores_l1_government-response.csv\ngovernment-response class 1–5]
    end

    A --> C
    A --> D
    A --> E

    B1 & C1 & D1 & E1 --> F

    subgraph TOPSIS["TOPSIS Aggregation"]
        F[topis_riskscore_district.py\nWeighted TOPSIS per month] --> G[risk_score.csv\nBlock-level risk score]
        G --> H[District aggregation\n+ indicator rollup]
        H --> I[risk_score_final_district.csv\nPlatform-ready output]
    end
```

---

## Document Index

| File | Score | Method | Script |
|------|-------|--------|--------|
| [score_hazard.md](./score_hazard.md) | Flood Hazard | Log-normalise + z-score + quantile bins | `hazard.py` |
| [score_exposure.md](./score_exposure.md) | Exposure | MinMax scale + std-dev bins | `exposure.py` |
| [score_vulnerability.md](./score_vulnerability.md) | Vulnerability | DEA (CRS) efficiency + Jenks breaks | `vulnerability.py` |
| [score_government_response.md](./score_government_response.md) | Government Response | FY cumulative sum + MinMax + std-dev bins | `govtresponse.py` |
| [topsis_risk_score.md](./topsis_risk_score.md) | Composite Risk | Weighted TOPSIS + district rollup | `topis_riskscore_district.py` |

---

## Common Input Requirements

All factor score scripts read from a single master CSV:

**File:** `RiskScoreModel/data/MASTER_VARIABLES.csv`

**Minimum required columns for all scripts:**

| Column | Type | Description |
|--------|------|-------------|
| `object_id` | Integer | Unique identifier for geographic unit (block/sub-district) |
| `timeperiod` | String | Month in `YYYY_MM` format |
| `district` | String | Parent administrative district name |
| *(factor-specific variables)* | Float | See individual score docs |

**Geographic unit:** Any consistent administrative unit (block, sub-district, revenue circle, etc.) that has a unique `object_id` and can be mapped to a district for aggregation.

**Temporal unit:** Monthly. The model runs independently per month, so time series length is flexible.

---

## Output Files

| File | Description |
|------|-------------|
| `factor_scores_l1_flood-hazard.csv` | Master variables + `flood-hazard` (1–5) + `flood-hazard-float` |
| `factor_scores_l1_exposure.csv` | Master variables + `exposure` (1–5) |
| `factor_scores_l1_vulnerability.csv` | Master variables + `vulnerability` (1–5) + `efficiency` |
| `factor_scores_l1_government-response.csv` | Master variables + `government-response` (1–5) |
| `risk_score.csv` | All factor scores + `TOPSIS_Score` + `risk-score` (1–5), block level |
| `risk_score_final_district.csv` | Block rows + district summary rows; platform-ready for IDS-DRR |
