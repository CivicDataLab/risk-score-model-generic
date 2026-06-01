# Intelligent Data Solution for Disaster Risk Reduction (IDS-DRR)

**An open-source model based on the Sendai DRR framework for computing flood risk scores from publicly available data.**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)](#status)

---

## Overview

Data that could enable more effective disaster-risk response and management is scattered or siloed across different agencies, at different scales and formats, making it difficult for decision-makers and relevant stakeholders to make data-informed decisions. The availability of good quality, machine-readable, and interoperable data is crucial for effective climate action and disaster response. However, in many contexts this data is fragmented across agencies, making timely, data-informed decisions difficult.

This repository contains the **risk-score model** of the IDS-DRR pipeline: a configurable system that combines climate, infrastructure access, losses & damages, procurement, and demographic data into a single composite flood risk score at district and sub-district (block/tehsil) levels. It is designed to be adapted to any geography for which the required input variables are available.

Originally developed for the state of Assam, India, this generic version of the codebase abstracts geography- and source-specific assumptions into configuration files so that the same scripts can be applied to other states, regions, or countries.

For programme background and methodological discussion, see the [project report](https://docs.google.com/document/d/12oSX3kltlaq1Wvxkc7GRjBkGbxu8hwpyASss7yB2dmc/edit?usp=sharing).

---

## Relevance to the Sustainable Development Goals

This work directly supports:

- **SDG 13 — Climate Action**, especially target 13.1 (strengthen resilience and adaptive capacity to climate-related hazards) and indicator 13.1.1 (number of people affected by disasters).
- **SDG 11 — Sustainable Cities and Communities**, especially target 11.5 (reduce deaths and economic losses caused by disasters) and target 11.b (integrated policies for resilience to disasters).

By producing transparent, reproducible risk scores at granular administrative levels, the project enables agencies to plan mitigation, target relief, and audit historical response patterns against measured exposure and vulnerability.

---

## What this repository contains

```
risk-score-model-generic/
├── scripts/             Factor and aggregation scripts (+ synthetic data generator)
├── config/              Generic, geography-neutral TOML configuration
├── data/                Synthetic sample input + district lookup; pipeline outputs
├── tests/               Automated tests (pytest)
├── docs/                Methodology documentation
├── contrib/             Region-specific tooling and examples
│   └── india/
│       ├── maps/        India admin-boundary download and transformation scripts
│       └── example/     India (Assam) reference configuration and dataset
│
├── CITATION.cff         Citation metadata
├── LICENSE              GNU AGPL v3.0
├── README.md
├── requirements.txt     Python runtime dependencies
└── requirements-dev.txt Development/test dependencies
```

The `config/` and `data/` at the root are **geography-neutral**: the bundled sample
is synthetic so the model runs out of the box on any machine. A complete real-world
configuration — the deployment the model was built for — lives under
[`contrib/india/example/`](contrib/india/example/).

This repository covers the **modelling layer** only. Data acquisition is handled by a companion repository — see [Data inputs](#data-inputs-and-the-flood-data-ecosystem) below.

---

## Architecture

```mermaid
flowchart LR
    subgraph DataLayer [Data Sources]
        S1[Rainfall]
        S2[Inundation]
        S3[Demographics]
        S4[Government tenders]
        S5[Losses and Damages]
    end

    DataLayer --> M[MASTER_VARIABLES.csv<br/>One row per unit per month]

    M --> H[hazard.py]
    M --> E[exposure.py]
    M --> V[vulnerability.py]
    M --> G[govtresponse.py]

    H --> T[topsis_riskscore.py<br/>TOPSIS aggregation]
    E --> T
    V --> T
    G --> T

    T --> O[risk_score_district.csv]
```

The four **factor scripts** (`hazard.py`, `exposure.py`, `vulnerability.py`, `govtresponse.py`) are independent and can run in any order. The **TOPSIS script** then combines their outputs into a single composite risk score weighted by hazard, exposure, vulnerability, and government response.

For a step-by-step walkthrough — including the input schema, configuration options, and per-script methodology — start with [`docs/getting_started.md`](docs/getting_started.md).

---

## Quick start

### Prerequisites

- Python 3.11 or later
- pip and a virtual-environment tool of your choice

### Install

```bash
git clone https://github.com/CivicDataLab/risk-score-model-generic.git
cd risk-score-model-generic
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the model with the bundled sample data

```bash
python scripts/hazard.py
python scripts/exposure.py
python scripts/vulnerability.py
python scripts/govtresponse.py
python scripts/topsis_riskscore.py
```

Each script reads `data/MASTER_VARIABLES.csv` (or the file named in your config) and writes a CSV under `data/`. The final composite is `data/risk_score_district.csv`.

The synthetic sample is committed, so the scripts run as-is. To regenerate it (it is deterministic), run:

```bash
python scripts/generate_sample_data.py
```

To run the bundled **India (Assam) reference example** instead of the synthetic sample, point the config-directory environment variable at it:

```bash
RISK_MODEL_CONFIG_DIR=contrib/india/example/config python scripts/hazard.py   # …and the rest
```

See [`contrib/india/example/`](contrib/india/example/) for details. To adapt the model to a new geography, follow [`docs/getting_started.md`](docs/getting_started.md).

---

## Configuration

Configuration TOML files are available under `config/`. The loader (`config/loader.py`) merges `base_config.toml` with the script-specific file at runtime:

| File | Controls |
|------|----------|
| `base_config.toml` | Input file path and shared column names (`object_id`, `timeperiod`, `district`) |
| `hazard_config.toml` | Hazard variables, quantile thresholds, output classes |
| `exposure_config.toml` | Exposure variables and class boundaries |
| `vulnerability_config.toml` | DEA input/output variables and polarity inversions |
| `govtresponse_config.toml` | Response variables and fiscal-year start month |
| `topsis_config.toml` | Factor weights, indicator aggregation rules, district lookup |

Adapting the model to a new geography is mostly a matter of editing these TOMLs to match your input data. Code changes are needed only when adding new factor variables or modifying the methodology.

---

## Documentation

| Document | Contents |
|----------|----------|
| [`getting_started.md`](docs/getting_started.md) | End-to-end guide for adapting the model to a new geography |
| [`score_hazard.md`](docs/score_hazard.md) | Flood Hazard methodology |
| [`score_exposure.md`](docs/score_exposure.md) | Exposure methodology |
| [`score_vulnerability.md`](docs/score_vulnerability.md) | Vulnerability methodology (DEA) |
| [`score_government_response.md`](docs/score_government_response.md) | Government Response methodology |
| [`topsis_risk_score.md`](docs/topsis_risk_score.md) | TOPSIS composite score and final output |
| [`dpg.md`](docs/dpg.md) | How the project maps to the Digital Public Goods Standard |
| [`contrib/india/example/`](contrib/india/example/) | India (Assam) reference configuration and dataset |
| [`contrib/india/maps/`](contrib/india/maps/) | admin-boundary download and transformation tooling for India |

---

## Data inputs and the Flood Data Ecosystem

The model consumes a single tabular file (`MASTER_VARIABLES.csv`) — one row per geographic unit per month. Each row carries the variables needed by the four factor scripts (rainfall, inundation, population, infrastructure, damages, expenditure).

The acquisition, cleaning, and joining of those variables is geography-specific. For the original India deployment it is handled by a companion repository:

➡️ **[CivicDataLab/flood-data-ecosystem-generic](https://github.com/CivicDataLab/flood-data-ecosystem-generic)**

That repository contains per-source extractors for the data sources used by the **India example** — the Indian Meteorological Department (IMD), ISRO Bhuvan, WorldPop, NASADEM, Mission Antyodaya, BharatMaps, WRIS, and government tender portals. Its output is a master CSV in the shape this model consumes. Adopters in other geographies supply their own equivalent sources; the model itself is agnostic to where the variables come from.

For testing and demonstration, this repository ships with a small **synthetic** sample dataset in `data/` (generated by `scripts/generate_sample_data.py`) so the model can be run end-to-end without any real data pipeline. A real-world Assam dataset is available under [`contrib/india/example/`](contrib/india/example/).

---

## Data extraction and interoperability

All inputs and outputs use non-proprietary, machine-readable formats:

- **Tabular data** — CSV (UTF-8) with documented schemas
- **Geometries** — GeoJSON in EPSG:4326 (WGS 84)
- **Configuration** — TOML
- **Documentation** — Markdown

Output columns and their semantics are documented inline in each methodology document and summarised in [`data/data_dictionary.csv`](data/data_dictionary.csv).


---

## Citation

If you use this work in research or operational practice, please cite it. A `CITATION.cff` file is included for reference managers; in plain text:

> CivicDataLab. (2026). *Intelligent Data Solution for Disaster Risk Reduction — Risk Score Model (Generic)*. https://github.com/CivicDataLab/risk-score-model-generic

---

## License

All source code in this repository is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0). The full license text is in [`LICENSE`](LICENSE).

[![GNU-AGPL](https://www.gnu.org/graphics/agplv3-155x51.png)](LICENSE)

Sample and derived datasets included in this repository are released under the **Creative Commons Attribution 4.0 International** license (CC-BY 4.0), unless a more restrictive licence applies to a specific upstream source (in which case the upstream licence governs that file).

---

## Status

This repository is in **beta**. The Assam-specific deployment is in production at scale; the generic refactor that lives here is being validated against new geographies. Interface and configuration schemas may still change between minor versions.

---

## Contact

CivicDataLab · <info@civicdatalab.in> · https://civicdatalab.in