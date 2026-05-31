# Reference Example — India (Assam)

This directory holds a complete, **real-world** configuration of the risk-score
model for the state of **Assam, India** — the deployment the model was originally
built for. It exists so adopters can see a fully-populated configuration and a
genuine input dataset rather than only the small synthetic sample in `data/`.

Everything here is India-specific and is intentionally kept *outside* the generic
core:

- **Government finance schemes** — SDRF (State Disaster Response Fund), SOPD, RIDF,
  LTIF, CIDF tender and expenditure columns.
- **Administrative concepts** — LGD `object_id` codes (`AA-BBB-CCCCC`), revenue-circle
  area (`rc_area`), embankment infrastructure, relief camps.
- **Fiscal calendar** — April–March (`fiscal_year.start_month = 4`).
- **Data sources** — IMD (rainfall), ISRO Bhuvan (inundation), WorldPop, NASADEM,
  Mission Antyodaya, BharatMaps, WRIS, and the Assam government tender/finance portals.

The administrative-boundary download and transformation tooling for India lives in
the sibling directory [`../maps/`](../maps/).

## Contents

```
config/   Full Assam configuration (all India-specific columns and schemes)
data/     Assam MASTER_VARIABLES.csv, district_objectid.csv, data_dictionary.csv,
          and Transformed_Assam_Data.csv
```

## Running the example

The scripts read their configuration directory from the `RISK_MODEL_CONFIG_DIR`
environment variable (see `config/loader.py`). Point it at this directory's
`config/` folder and run the pipeline from the repository root:

```bash
# from the repository root
export RISK_MODEL_CONFIG_DIR=contrib/india/example/config

python scripts/hazard.py
python scripts/exposure.py
python scripts/vulnerability.py
python scripts/govtresponse.py
python scripts/topsis_riskscore.py
```

All inputs are read from, and all outputs are written to,
`contrib/india/example/data/` (configured via `paths` in the example's
`base_config.toml` and `topsis_config.toml`). The generated factor-score and
risk-score CSVs are git-ignored.

To return to the generic synthetic sample, simply unset the variable:

```bash
unset RISK_MODEL_CONFIG_DIR
```

## License

The Assam sample/derived datasets in this directory are released under
**Creative Commons Attribution 4.0 International** (CC-BY 4.0), unless a more
restrictive licence applies to a specific upstream source, in which case the
upstream licence governs that file.
