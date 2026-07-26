"""
app/ml/evaluation.py

Contains logic for evaluating model metrics assuming a realistic SOC analyst alert budget.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)

def evaluate_budget_metrics(df: pd.DataFrame, score_col: str, label_col: str, top_k_pct: float = 0.01) -> dict:
    """
    Evaluates Precision, Recall, and FPR assuming a fixed SOC analyst budget.
    We take the top 'top_k_pct' (e.g. 1%) of events sorted by anomaly score,
    and treat those as the 'alerts'.

    Args:
        df: The dataframe with scores and ground-truth labels.
        score_col: Column containing raw anomaly scores (lower = more anomalous).
        label_col: Column containing ground-truth labels.
        top_k_pct: Percentage of total events analysts have capacity to review.
    
    Returns:
        dict: containing Precision, Recall, and FPR.
    """
    if label_col not in df.columns:
        logger.info(f"Skipping budget metrics: '{label_col}' not found.")
        return {}

    if df.empty:
        return {}

    n_total = len(df)
    n_budget = max(1, int(n_total * top_k_pct))

    # Sort so most anomalous (lowest score) are at the top
    sorted_df = df.sort_values(by=score_col, ascending=True)

    # Top K events are what the SOC actually reviews
    budget_alerts = sorted_df.head(n_budget)

    # True labels: assume 'Normal' is negative, anything else is positive
    is_anomaly = df[label_col].str.lower() != 'normal'
    actual_positives = is_anomaly.sum()
    actual_negatives = n_total - actual_positives

    # True positives within the budget
    tp = (budget_alerts[label_col].str.lower() != 'normal').sum()
    fp = n_budget - tp

    precision = tp / n_budget if n_budget > 0 else 0.0
    recall = tp / actual_positives if actual_positives > 0 else 0.0
    fpr = fp / actual_negatives if actual_negatives > 0 else 0.0

    metrics = {
        "budget_n": n_budget,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "fpr": round(fpr, 6)
    }

    logger.info(f"Budget Evaluation (Top {top_k_pct*100}% = {n_budget} alerts):")
    logger.info(f"  Precision: {metrics['precision']:.2f}")
    logger.info(f"  Recall:    {metrics['recall']:.2f}")
    logger.info(f"  FPR:       {metrics['fpr']:.4f}")

    return metrics
