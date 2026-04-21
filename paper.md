---
title: 'FIRM Tool: an interactive clinical decision support tool for febrile infant risk stratification in resource-limited emergency departments'
tags:
  - Python
  - Streamlit
  - clinical decision support
  - febrile infant
  - invasive bacterial infection
  - rural emergency medicine
  - prediction model
authors:
  - name: Hayden Farquhar
    orcid: 0009-0002-6226-440X
    affiliation: 1
affiliations:
  - name: Independent Researcher, Finley, New South Wales, Australia
    index: 1
date: 19 April 2026
bibliography: paper.bib
---

# Summary

The FIRM Tool (Febrile Infant Rural Model) is an interactive web-based clinical decision support application for emergency clinicians managing febrile infants aged 0--89 days. It generates a continuous probability estimate of invasive bacterial infection (IBI --- bacteraemia or bacterial meningitis) from clinical and laboratory inputs routinely available in rural and regional emergency departments, without requiring procalcitonin or a complete laboratory panel. The tool assigns each infant to one of four risk tiers (very low, low, moderate, high), compares the predicted risk against residual IBI rates from five published decision rules, and provides age-specific clinical context aligned with current guideline recommendations. Missing laboratory inputs are handled through median imputation rather than binary exclusion, allowing the tool to degrade gracefully when tests are unavailable.

# Statement of need

Febrile infants under 90 days are a common and high-stakes presentation in emergency departments. Approximately 2% harbour an invasive bacterial infection, but distinguishing these from the majority with self-limiting viral illness is difficult on clinical grounds alone [@pantell2004]. Several validated decision rules --- including PECARN [@kuppermann2019], the Aronson criteria [@aronson2019], the Step-by-Step algorithm [@gomez2016], and the AAP 2021 guideline [@pantell2021] --- have been developed to stratify IBI risk. However, all assume access to a full panel of investigations, typically including procalcitonin, C-reactive protein, automated differential, and urinalysis.

In rural and regional emergency departments, one or more of these inputs is frequently unavailable. Procalcitonin is not offered at most rural Australian laboratories [@aacb2019]. Point-of-care testing may provide only a total white cell count. When a required input is missing, the existing rules offer no guidance: the clinician must either apply the rule with incomplete data (invalidating its operating characteristics) or default to full investigation and transfer regardless of the infant's clinical presentation. Neither approach is satisfactory.

The FIRM Tool addresses this gap by providing a continuous probability estimate that quantifies how each missing input affects the risk estimate, rather than treating missing data as a binary exclusion criterion. This allows clinicians to make informed decisions about local management versus transfer based on the actual information available.

No existing tool fills this niche. Published decision rules produce binary outputs (low-risk or not) and require complete input panels. The FIRM Tool is the first to provide a continuous, context-rich probability estimate designed specifically for incomplete-data scenarios in resource-limited settings.

# Software design

The FIRM Tool is implemented as a Streamlit web application in Python. The prediction model is a logistic regression with seven predictors (age, temperature, white blood cell count, absolute neutrophil count, urinalysis result, Yale Observation Scale score, and a neonatal age indicator), derived from the PECARN Biosignatures public-use dataset (n=4,434; 88 IBI events) [@kuppermann2019]. Model coefficients are embedded directly in the source code, eliminating external dependencies on data files or serialised model objects. This design choice ensures full reproducibility and portability: the tool can be deployed on any platform that supports Python and Streamlit.

The application architecture consists of three components:

1. **Prediction engine** (`src/prediction_model.py`): Computes IBI probability from embedded logistic regression coefficients. Missing inputs are imputed with training-set medians. Returns a structured result containing the probability, risk tier, clinical context, and rule comparisons.

2. **Published rule implementations** (`src/rules/`): Seven decision rules (Rochester, Philadelphia, Step-by-Step, PECARN, Aronson, AAP 2021, NICE NG143) implemented as pure Python functions. Each returns a structured result indicating whether the rule is applicable with the available inputs and, if so, the classification.

3. **Interactive interface** (`streamlit_app.py`): A two-column layout with clinical input controls (sidebar) and assessment output (main panel). Displays the continuous probability, risk tier with colour coding, published rule comparisons, and age-specific guideline context.

The tool is deployed on Streamlit Community Cloud for zero-installation browser access and is also runnable locally via `streamlit run streamlit_app.py`.

# Research context

The derivation study and internal validation of the FIRM model are reported in a separate manuscript [@farquhar2026preprint], currently under peer review at *Archives of Disease in Childhood* (MS# archdischild-2026-330835). The derivation study combines a bivariate HSROC meta-analysis of seven published febrile infant decision rules with individual-level prediction modelling. The model achieved an optimism-corrected AUC of 0.780 (bootstrap 95% CI 0.705--0.853) and calibration slope of 0.937. At the 1.5% probability threshold, 66% of infants were classified into actionable risk tiers with an observed IBI rate of 0.68% in the combined very-low and low-risk groups. The full analysis code is archived separately [@farquhar2026code].

The FIRM Tool has not been externally validated. A three-phase validation programme is proposed: retrospective external validation on an Australian cohort, prospective silent-mode deployment in rural emergency departments, and a clinical impact study. We invite the PREDICT network and other paediatric emergency research groups to undertake prospective validation.

# AI usage disclosure

Claude Code (Anthropic, Claude Opus 4) was used for assistance with Python coding, Streamlit interface development, and initial manuscript drafting. All analytical decisions, clinical interpretations, and final content were reviewed and approved by the author.

# Acknowledgements

The PECARN Biosignatures public-use dataset was accessed under a Research Data Use Agreement from the PECARN Data Coordinating Center.

# References
