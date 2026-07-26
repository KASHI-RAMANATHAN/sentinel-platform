"""
app/ml

Core Machine Learning package for Sentinel.

This package implements the full anomaly detection and threat classification pipeline:
    - feature_engineering.py: Transforms raw logs into model features, handles encoding, and implements cold-start entity handling.
    - baseline_model.py: Builds user behavior profiles from historical data.
    - anomaly_detector.py: Unsupervised IsolationForest model for anomaly detection.
    - attack_classifier.py: Supervised RandomForest model for attack-type classification.
    - explainability.py: Rule-based/SHAP explanations for predictions.
    - inference_engine.py: Singleton engine for real-time inference and SHAP-based explanations.
    - evaluation.py: Computes precision, recall, and FPR at a fixed analyst alert budget.
    - pipeline.py: Orchestrates the full batch ML pipeline for all models.

This package IS wired into the API via app/services/prediction_service.py and
app/api/predict.py, returning real (not stubbed) predictions.
"""
