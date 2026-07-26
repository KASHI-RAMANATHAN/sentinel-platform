"""
app/ml/risk_scoring.py

PLACEHOLDER — Final risk scoring.

Future scope:
- Combine anomaly_detection score, attack_classification confidence,
  and contextual signals (user role, asset sensitivity, historical
  baseline) into a single normalized 0-1 risk score.
- Define severity thresholds (low/medium/high/critical) mapping the
  numeric score to AlertSchema.severity.
- Output feeds PredictionResponse.risk_score and is used by
  alert_service.py when auto-creating alerts.

No implementation yet — intentionally left as a stub for the
hackathon's ML phase.
"""


def compute_risk_score(*args, **kwargs):
    """TODO: Implement composite risk scoring logic."""
    raise NotImplementedError("Risk scoring not yet implemented.")
