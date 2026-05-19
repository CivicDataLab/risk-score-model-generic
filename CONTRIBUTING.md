# Contributing to IDS-DRR Risk Score Model

Thank you for your interest in contributing. This project is maintained by [CivicDataLab](https://civicdatalab.in) and we welcome contributions from researchers, practitioners, and civic technologists.

---

## Ways to contribute

| Type | How |
|------|-----|
| Bug reports | Open a GitHub issue |
| Methodology improvements | Open an issue first, then a PR with a rationale note |
| New geography adaptations | Share config files and a brief validation summary |
| Documentation fixes | PR directly against `main` |
| Questions and partnerships | Email <info@civicdatalab.in> |

---

## Before you open a pull request

1. **Check for an open issue.** Search [existing issues](https://github.com/CivicDataLab/risk-score-model-generic/issues) before opening a new one to avoid duplication.
2. **For non-trivial changes, open an issue first.** This lets us align on scope before you invest time writing code.
3. **Reference the issue in your PR description.** Use `Closes #<issue-number>` or `Relates to #<issue-number>`.

---

## Development setup

```bash
git clone https://github.com/CivicDataLab/risk-score-model-generic.git
cd risk-score-model-generic
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the model end-to-end against the bundled sample data to confirm your environment is working:

```bash
python scripts/hazard.py
python scripts/exposure.py
python scripts/vulnerability.py
python scripts/govtresponse.py
python scripts/topsis_riskscore.py
```

---

## Submitting a pull request

1. Fork the repository and create a branch from `main`.
2. Make your changes. Keep commits focused — one logical change per commit.
3. Confirm that the end-to-end pipeline still produces output without errors.
4. Open a PR against `main` with a clear title and a brief description of what changed and why.

---

## Proposing methodological changes

The scoring methodology (factor weights, normalisation approach, DEA setup, TOPSIS aggregation) has implications for operational decisions downstream. Before proposing a change:

- Attach a short note explaining the rationale — what problem does the change address?
- Where possible, cite empirical evidence or literature that supports the change.
- If the change affects numerical outputs, include a comparison of scores before and after (even on the sample dataset) so reviewers can assess the magnitude.

---

## Code style

- Python 3.11+, no enforced formatter — match the style of the file you are editing.
- Avoid adding dependencies not in `requirements.txt` without discussion.
- Configuration changes (new variables, thresholds, column names) belong in TOML config files, not hardcoded in scripts.

---

## License

By contributing, you agree that your contributions will be licensed under the [GNU AGPL v3.0](LICENSE). Sample and derived data contributions are accepted under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/).
