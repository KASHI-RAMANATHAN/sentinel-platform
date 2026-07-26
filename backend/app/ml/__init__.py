"""
app/ml

PLACEHOLDER PACKAGE — no ML implementation yet.

This package will eventually hold the full anomaly detection pipeline:
    1. dataset_generation.py     - synthetic/sample behavioral dataset creation
    2. feature_engineering.py    - transforming raw logs into model features
    3. anomaly_detection.py      - unsupervised/supervised anomaly detection models
    4. attack_classification.py  - classifying detected anomalies into attack types
    5. explainability.py         - SHAP/LIME-based explanations for predictions
    6. risk_scoring.py           - combining signals into a final 0-1 risk score

Nothing in this package is wired into the API yet — app/services/
prediction_service.py currently returns stubbed responses.
"""
