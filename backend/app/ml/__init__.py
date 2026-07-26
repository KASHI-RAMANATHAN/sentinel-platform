"""
app/ml

PLACEHOLDER PACKAGE — no ML implementation yet.

This package will eventually hold the full anomaly detection pipeline:
    1. feature_engineering.py    - transforming raw logs into model features
    2. anomaly_detection.py      - unsupervised/supervised anomaly detection models
    3. attack_classification.py  - classifying detected anomalies into attack types
    4. explainability.py         - SHAP/LIME-based explanations for predictions

Nothing in this package is wired into the API yet — app/services/
prediction_service.py currently returns stubbed responses.
"""
