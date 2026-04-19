# Contributing to the FIRM Tool

Thank you for your interest in contributing to the FIRM Tool. This document describes how to set up the development environment, run tests, and submit changes.

## Development setup

```bash
git clone https://github.com/hayden-farquhar/FIRM-tool.git
cd FIRM-tool
pip install -r requirements.txt
pip install pytest
```

## Running the tool locally

```bash
streamlit run streamlit_app.py
```

## Running tests

```bash
python -m pytest tests/ -v
```

All tests must pass before submitting a pull request.

## Project structure

```
FIRM-tool/
├── streamlit_app.py          # Streamlit web interface
├── src/
│   ├── prediction_model.py   # FIRM model with embedded coefficients
│   └── rules/                # Published decision rule implementations
│       ├── aronson.py        # Aronson et al. 2019
│       ├── pecarn.py         # Kuppermann et al. 2019
│       ├── step_by_step.py   # Gomez et al. 2016
│       ├── aap_2021.py       # Pantell et al. 2021
│       ├── rochester.py      # Jaskiewicz & McCarthy 1994
│       ├── philadelphia.py   # Baker et al. 1993
│       └── nice_ng143.py     # NICE NG143 2019
├── tests/
│   ├── test_prediction_model.py  # 30 tests for the FIRM model
│   └── test_rules.py            # 21 tests for decision rules
├── paper.md                  # JOSS software paper
└── paper.bib                 # References for JOSS paper
```

## How the model works

The FIRM model is a logistic regression with 7 predictors. The model coefficients are embedded directly in `src/prediction_model.py` (no external model files). The `predict()` function takes clinical inputs, imputes missing values with training-set medians, computes the logit, and returns a `PredictionResult` with the probability, risk tier, and clinical context.

## Adding or modifying decision rules

Each rule in `src/rules/` follows the same pattern:

1. An `*Inputs` dataclass defining the required inputs
2. A `RuleResult` dataclass with `prediction` (0=low-risk, 1=not-low-risk), `triggered_criteria`, and `applicable`
3. An `apply()` function that returns a `RuleResult`

When adding a new rule, also add corresponding tests in `tests/test_rules.py`.

## Types of contributions welcome

- **External validation results**: if you apply the FIRM model to a local cohort, we are very interested in the results
- **Bug fixes**: corrections to rule implementations or model code
- **Documentation improvements**: clearer explanations, additional examples
- **New decision rules**: implementations of other validated febrile infant rules
- **Translations**: the clinical context messages could be translated for non-English settings

## Reporting issues

Please open an issue on GitHub describing:
- What you expected to happen
- What actually happened
- Steps to reproduce (if applicable)
- Your Python version and operating system

## Clinical validation

If you are planning a prospective validation study of the FIRM tool, please contact the author (hayden.farquhar@icloud.com) so we can coordinate and avoid duplication of effort.

## Code of conduct

Be respectful and constructive. This is a clinical tool — accuracy and safety are paramount.
