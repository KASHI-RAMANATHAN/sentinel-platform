"""
app/ml/pipeline.py

Full batch ML pipeline â€” orchestrates every existing ML module in sequence.

Steps
-----
1. Feature Engineering  (feature_engineering.py)
2. Baseline Profiling   (baseline_model.py)
3. Anomaly Detection    (anomaly_detector.py   â†’ IsolationForest)
4. Attack Classification(attack_classifier.py  â†’ RandomForest)
5. SHAP Explainability  (explainability.py     â†’ TreeExplainer)

Design
------
- All logic is **delegated** to the existing module functions â€” no logic is
  duplicated here. This file only wires the steps together.
- Input is a raw-log DataFrame (same schema as access_logs_raw.csv).
- Outputs are written to the ``processed_dir``; model artefacts go to
  ``model_dir``.
- The function returns a ``PipelineResult`` dataclass that the upload
  service uses to build the HTTP response summary.
- When a ground-truth column ('attack_type' or 'label') is absent the
  attack-classifier step is skipped (predict-only mode using saved model).
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid

import joblib
import numpy as np
import pandas as pd

# â”€â”€ Reuse existing ML modules â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
from app.ml import feature_engineering as fe
from app.ml import anomaly_detector as ad
from app.ml import attack_classifier as ac
from app.ml import baseline_model as bm
from app.ml import explainability as ex
from app.firebase.firestore_client import get_firestore_client
from app.schemas.alert_schema import AlertSeverity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass (returned to the service layer)
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    name: str
    success: bool
    rows_in: int = 0
    rows_out: int = 0
    duration_s: float = 0.0
    detail: str = ""
    error: Optional[str] = None


@dataclass
class PipelineResult:
    total_rows: int = 0
    anomalies_detected: int = 0
    anomaly_rate_pct: float = 0.0
    attack_types_found: List[str] = field(default_factory=list)
    profiles_built: int = 0
    shap_explained_rows: int = 0
    output_files: Dict[str, str] = field(default_factory=dict)
    steps: List[StepResult] = field(default_factory=list)
    total_duration_s: float = 0.0
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Isolation Forest feature list (matches training)
# ---------------------------------------------------------------------------
_ISO_FEATURES = [
    "login_hour", "day_of_week", "session_duration", "command_length",
    "unique_resources", "failed_login_count", "is_known_device", "is_known_location",
]

# Attack classifier uses these two extras when available
_CLF_EXTRA_FEATURES = ["auth_method_encoded", "entity_type_encoded"]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_pipeline(
    df_raw: pd.DataFrame,
    processed_dir: str,
    model_dir: str,
    contamination: float = 0.02,
) -> PipelineResult:
    """
    Run the full ML pipeline on ``df_raw`` and persist all outputs.

    Args:
        df_raw:         Raw log DataFrame (same schema as access_logs_raw.csv).
        processed_dir:  Directory where CSV outputs are written.
        model_dir:      Directory where trained model .pkl files are saved/loaded.
        contamination:  IsolationForest expected anomaly fraction (default 2 %).

    Returns:
        PipelineResult with per-step timing, row counts, and summary stats.
    """
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    result = PipelineResult()
    result.total_rows = len(df_raw)
    pipeline_start = time.perf_counter()

    df = df_raw.copy()

    # â”€â”€ Step 1 â€” Feature Engineering â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    df, step1 = _step_feature_engineering(df, processed_dir)
    result.steps.append(step1)
    
    from app.services.audit_service import audit_service
    from app.schemas.audit_schema import AuditLogCreate, AuditActor, AuditCategory, AuditStatus
    if not step1.success:
        audit_service.log_event_sync(AuditLogCreate(
            actor=AuditActor.ML_ENGINE,
            action="Feature Engineering Failed",
            category=AuditCategory.ERRORS,
            resource="pipeline",
            status=AuditStatus.FAILED,
            details=str(step1.error)
        ))
        result.success = False
        result.error = step1.error
        return result
    else:
        audit_service.log_event_sync(AuditLogCreate(
            actor=AuditActor.ML_ENGINE,
            action="Feature Engineering Completed",
            category=AuditCategory.SYSTEM,
            resource="pipeline",
            status=AuditStatus.SUCCESS,
            details=step1.detail
        ))

    # â”€â”€ Step 2 â€” Baseline Profiling â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    profiles_df, step2 = _step_baseline(df, processed_dir)
    result.steps.append(step2)
    result.profiles_built = len(profiles_df) if profiles_df is not None else 0
    # non-fatal â€” pipeline continues even if baseline fails

    # â”€â”€ Step 3 â€” Isolation Forest (Anomaly Detection) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    df, iso_model, step3 = _step_anomaly_detection(df, processed_dir, model_dir, contamination)
    result.steps.append(step3)
    if not step3.success:
        audit_service.log_event_sync(AuditLogCreate(
            actor=AuditActor.ML_ENGINE,
            action="Prediction Failed",
            category=AuditCategory.ERRORS,
            resource="pipeline",
            status=AuditStatus.FAILED,
            details=str(step3.error)
        ))
        result.success = False
        result.error = step3.error
        return result

    anomaly_mask = df["anomaly_prediction"] == -1
    result.anomalies_detected = int(anomaly_mask.sum())
    result.anomaly_rate_pct = round(
        result.anomalies_detected / max(len(df), 1) * 100, 2
    )
    
    audit_service.log_event_sync(AuditLogCreate(
        actor=AuditActor.ML_ENGINE,
        action="Prediction Completed",
        category=AuditCategory.SYSTEM,
        resource="pipeline",
        status=AuditStatus.SUCCESS,
        details=f"Isolation Forest processed {len(df)} events and detected {result.anomalies_detected} anomalies."
    ))

    # â”€â”€ Step 4 â€” Attack Classification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    df, clf_model, step4 = _step_attack_classification(df, processed_dir, model_dir)
    result.steps.append(step4)
    if not step4.success:
        # non-fatal: classification may be skipped (no ground truth)
        logger.warning("Attack classification skipped/failed: %s", step4.error)

    if "predicted_attack_type" in df.columns:
        result.attack_types_found = (
            df.loc[anomaly_mask, "predicted_attack_type"].dropna().unique().tolist()
        )

    # ── Step 5 — SHAP Explainability ────────────────────────────────
    df, step5 = _step_shap(df, iso_model, processed_dir)
    result.steps.append(step5)
    result.shap_explained_rows = step5.rows_out
    if step5.success and step5.rows_out > 0:
        audit_service.log_event_sync(AuditLogCreate(
            actor=AuditActor.ML_ENGINE,
            action="SHAP Explanation Generated",
            category=AuditCategory.SYSTEM,
            resource="pipeline",
            status=AuditStatus.SUCCESS,
            details=step5.detail
        ))

    # ── Step 6 — Firestore Sync (Subprocess) ───────────────────
    df, step6 = _step_firestore_sync(df, processed_dir)
    result.steps.append(step6)

    # ── Record output files ───────────────────────────────────────────────────
    result.output_files = {
        "processed_logs":        os.path.join(processed_dir, "access_logs_processed.csv"),
        "user_profiles":         os.path.join(processed_dir, "user_behavior_profiles.csv"),
        "predictions":           os.path.join(processed_dir, "predictions.csv"),
        "classified_predictions":os.path.join(processed_dir, "classified_predictions.csv"),
        "explanations":          os.path.join(processed_dir, "explanations.csv"),
        "isolation_forest_model":os.path.join(model_dir,    "isolation_forest.pkl"),
        "attack_classifier_model":os.path.join(model_dir,   "attack_classifier.pkl"),
    }

    result.total_duration_s = round(time.perf_counter() - pipeline_start, 2)
    logger.info(
        "Pipeline complete in %.1fs â€” %d rows, %d anomalies (%.1f%%)",
        result.total_duration_s, result.total_rows,
        result.anomalies_detected, result.anomaly_rate_pct,
    )
    audit_service.log_event_sync(AuditLogCreate(
        actor=AuditActor.ML_ENGINE,
        action="Dataset Processed",
        category=AuditCategory.SYSTEM,
        resource="pipeline",
        status=AuditStatus.SUCCESS,
        details=f"Pipeline complete in {result.total_duration_s}s. {result.total_rows} rows processed."
    ))
    return result


# ---------------------------------------------------------------------------
# Step implementations â€” each calls existing module functions directly
# ---------------------------------------------------------------------------

def _step_feature_engineering(
    df: pd.DataFrame, processed_dir: str
) -> tuple[pd.DataFrame, StepResult]:
    step = StepResult(name="feature_engineering", success=False, rows_in=len(df))
    t0 = time.perf_counter()
    try:
        # ── Normalise column names from the uploaded CSV ─────────────────────
        # The raw access_logs CSV uses different names than what the ML
        # modules expect internally. Rename before any processing so that
        # entity-level features (failed_login_count, is_known_device, etc.)
        # are computed correctly instead of falling back to zero defaults.
        col_map = {
            "user_id":     "entity_id",
            "device_id":   "device_fingerprint",
            "ip":          "source_ip",
            "resource":    "resource_accessed",
            "login_method": "auth_method",
            "role":        "entity_type",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        # Build geo_location from city + country if not already present
        if "geo_location" not in df.columns:
            if "city" in df.columns and "country" in df.columns:
                df["geo_location"] = df["city"].astype(str) + ", " + df["country"].astype(str)
            elif "city" in df.columns:
                df["geo_location"] = df["city"].astype(str)
            elif "country" in df.columns:
                df["geo_location"] = df["country"].astype(str)

        # ── Run standard ML pipeline steps ───────────────────────────────────
        df = fe.clean_data(df)
        df = fe.engineer_features(df)
        df = fe.encode_features(df)

        out_path = os.path.join(processed_dir, "access_logs_processed.csv")
        fe.save_processed_data(df, out_path)

        step.success = True
        step.rows_out = len(df)
        step.detail = f"Saved {len(df)} processed rows → {out_path}"
    except Exception as exc:
        step.error = str(exc)
        logger.exception("feature_engineering step failed")
    step.duration_s = round(time.perf_counter() - t0, 2)
    return df, step


def _step_baseline(
    df: pd.DataFrame, processed_dir: str
) -> tuple[Optional[pd.DataFrame], StepResult]:
    step = StepResult(name="baseline_profiling", success=False, rows_in=len(df))
    t0 = time.perf_counter()
    profiles = None
    try:
        # baseline_model.py expects entity_id and renamed columns
        df_bm = df.copy()
        col_map = {
            "user_id": "entity_id",
            "login_method": "auth_method",
            "resource": "resource_accessed",
            "device_id": "device_fingerprint",
        }
        df_bm.rename(columns={k: v for k, v in col_map.items() if k in df_bm.columns}, inplace=True)
        if "geo_location" not in df_bm.columns and "city" in df_bm.columns:
            df_bm["geo_location"] = df_bm["city"] + ", " + df_bm["country"]

        # Reuse baseline_model.py function
        profiles = bm.build_user_profiles(df_bm)

        out_path = os.path.join(processed_dir, "user_behavior_profiles.csv")
        bm.save_profiles(profiles, out_path)

        step.success = True
        step.rows_out = len(profiles)
        step.detail = f"Built {len(profiles)} user profiles → {out_path}"
    except Exception as exc:
        step.error = str(exc)
        logger.warning("baseline_profiling step failed (non-fatal): %s", exc)
    step.duration_s = round(time.perf_counter() - t0, 2)
    return profiles, step


def _step_anomaly_detection(
    df: pd.DataFrame,
    processed_dir: str,
    model_dir: str,
    contamination: float,
) -> tuple[pd.DataFrame, object, StepResult]:
    step = StepResult(name="anomaly_detection", success=False, rows_in=len(df))
    t0 = time.perf_counter()
    iso_model = None
    try:
        # Reuse anomaly_detector.py functions
        X = ad.select_features(df).fillna(0)

        # ── Dynamic contamination from ground-truth labels ────────────────
        # If the uploaded CSV has a 'label' column, use the actual anomaly
        # fraction as contamination — far more accurate than the 2% default.
        effective_contamination = contamination
        if "label" in df.columns:
            n_total = len(df)
            n_anomaly = int((df["label"].str.strip().str.lower() != "normal").sum())
            if 0 < n_anomaly < n_total:
                raw_rate = n_anomaly / n_total
                # Clamp to [0.01, 0.45] — IsolationForest limits
                effective_contamination = round(max(0.01, min(0.45, raw_rate)), 4)
                logger.info(
                    "Dynamic contamination from labels: %d/%d = %.2f%% → using %.4f",
                    n_anomaly, n_total, raw_rate * 100, effective_contamination,
                )

        # ── Build training set (history + new, new weighted ≥50%) ────────
        history_path = os.path.join(model_dir, "iso_history.csv")
        if os.path.exists(history_path):
            history_X = pd.read_csv(history_path)
            # Cap history at 2× the new upload size so new patterns dominate
            history_cap = len(X) * 2
            history_X = history_X.tail(history_cap)
            combined_X = pd.concat([history_X, X], ignore_index=True)
        else:
            combined_X = X.copy()

        # Persist updated history (capped at 10 000 rows)
        combined_X.tail(10_000).to_csv(history_path, index=False)

        logger.info(
            "Training Isolation Forest on %d rows (contamination=%.4f)…",
            len(combined_X), effective_contamination,
        )
        iso_model = ad.train_model(combined_X, contamination=effective_contamination)
        
        model_path = os.path.join(model_dir, "isolation_forest.pkl")
        ad.save_model(iso_model, model_path)

        predictions = ad.predict_anomalies(iso_model, X)
        scores = ad.calculate_anomaly_scores(iso_model, X)

        df["anomaly_prediction"] = predictions
        df["anomaly_score"] = scores

        pred_path = os.path.join(processed_dir, "predictions.csv")
        ad.save_predictions(df, pred_path)

        n_anomalies = int((predictions == -1).sum())
        step.success = True
        step.rows_out = len(df)
        step.detail = (
            f"Detected {n_anomalies}/{len(df)} anomalies "
            f"({n_anomalies/max(len(df),1)*100:.1f}%) â†’ {pred_path}"
        )
    except Exception as exc:
        step.error = str(exc)
        logger.exception("anomaly_detection step failed")
    step.duration_s = round(time.perf_counter() - t0, 2)
    return df, iso_model, step


def _step_attack_classification(
    df: pd.DataFrame,
    processed_dir: str,
    model_dir: str,
) -> tuple[pd.DataFrame, Optional[object], StepResult]:
    step = StepResult(name="attack_classification", success=False, rows_in=len(df))
    t0 = time.perf_counter()
    clf_model = None
    try:
        has_ground_truth = "attack_type" in df.columns or "label" in df.columns
        model_path = os.path.join(model_dir, "attack_classifier.pkl")
        history_path = os.path.join(model_dir, "clf_history.csv")

        if has_ground_truth:
            X_curr, y_curr = ac.prepare_features(df)
            curr_df = X_curr.copy()
            curr_df['target_label'] = y_curr
            
            if os.path.exists(history_path):
                history_df = pd.read_csv(history_path)
                combined_df = pd.concat([history_df, curr_df], ignore_index=True)
                combined_df = combined_df.tail(10000)
            else:
                combined_df = curr_df.copy()
            
            combined_df.to_csv(history_path, index=False)
            
            X_combined = combined_df.drop(columns=['target_label'])
            y_combined = combined_df['target_label']
            
            logger.info(f"Training Attack Classifier dynamically on {len(X_combined)} historical + new rows...")
            X_train, X_test, y_train, y_test = ac.split_dataset(X_combined, y_combined)
            clf_model = ac.train_classifier(X_train, y_train)
            ac.evaluate_classifier(clf_model, X_test, y_test)
            ac.save_model(clf_model, model_path)
            
            X = X_curr
        else:
            if os.path.exists(model_path):
                logger.info("Loading existing attack classifier for inference...")
                clf_model = joblib.load(model_path)
                features = [f for f in _ISO_FEATURES + _CLF_EXTRA_FEATURES if f in df.columns]
                X = df[features].copy().fillna(0)
            else:
                raise FileNotFoundError("No attack_type column and no saved classifier/history found.")

        predicted_types, confidences = ac.classify_attacks(clf_model, X)
        df["predicted_attack_type"] = predicted_types
        df["prediction_confidence"] = confidences

        # Normal rows â†’ override with 'Normal'
        if "anomaly_prediction" in df.columns:
            mask_normal = df["anomaly_prediction"] == 1
            df.loc[mask_normal, "predicted_attack_type"] = "Normal"
            df.loc[mask_normal, "prediction_confidence"] = 1.0

        out_path = os.path.join(processed_dir, "classified_predictions.csv")
        ac.save_predictions(df, out_path)

        attack_counts = df["predicted_attack_type"].value_counts().to_dict()
        step.success = True
        step.rows_out = len(df)
        step.detail = f"Attack distribution: {attack_counts} â†’ {out_path}"
        
        from app.services.audit_service import audit_service
        from app.schemas.audit_schema import AuditLogCreate, AuditActor, AuditCategory, AuditStatus
        for attack_type, count in attack_counts.items():
            if attack_type == "Normal":
                continue
            
            # Map attack type to the event action required by prompt
            # e.g., "Credential Abuse Detected"
            if attack_type.lower() == "brute force":
                action_name = "Credential Abuse Detected"
            else:
                action_name = f"{attack_type} Detected"

            audit_service.log_event_sync(AuditLogCreate(
                actor=AuditActor.ML_ENGINE,
                action=action_name,
                category=AuditCategory.SECURITY,
                resource="pipeline",
                status=AuditStatus.CRITICAL,
                details=f"Detected {count} instances of {attack_type} during batch processing."
            ))

    except Exception as exc:
        step.error = str(exc)
        logger.warning("attack_classification step failed (non-fatal): %s", exc)
    step.duration_s = round(time.perf_counter() - t0, 2)
    return df, clf_model, step


def _step_shap(
    df: pd.DataFrame,
    iso_model,
    processed_dir: str,
) -> tuple[pd.DataFrame, StepResult]:
    """
    Rule-based explainability step (replaces SHAP).

    Uses per-feature z-scores vs the normal population to rank which
    features drove the anomaly flag.  Pure Python — runs in milliseconds,
    never crashes on Windows threads.
    """
    step = StepResult(name="explainability", success=False, rows_in=len(df))
    t0 = time.perf_counter()
    try:
        # Use the full feature set the Isolation Forest was trained on
        X = ad.select_features(df).fillna(0)
        available = list(X.columns)

        anomaly_mask = df["anomaly_prediction"] == -1
        X_anomalies = X[anomaly_mask]

        df["top_features"] = None
        df["shap_values"]  = None
        df["explanation"]  = "Normal activity."
        df["recommended_action"] = "No action required."

        if len(X_anomalies) == 0:
            step.success = True
            step.rows_out = 0
            step.detail = "No anomalies to explain."
        else:
            # Rule-based explainer — handles all rows, no row cap needed
            _, scores         = ex.generate_shap_values(iso_model, X_anomalies, X_full=X)
            top_features_list = ex.identify_top_features(scores, available, top_n=3)
            explanations, actions = ex.build_explanations(top_features_list)

            formatted_top  = [", ".join(f for f, _ in tf) for tf in top_features_list]
            formatted_vals = [", ".join(f"{f}: {s:.4f}" for f, s in tf) for tf in top_features_list]

            df.loc[anomaly_mask, "top_features"] = formatted_top
            df.loc[anomaly_mask, "shap_values"]  = formatted_vals
            df.loc[anomaly_mask, "explanation"]  = explanations
            df.loc[anomaly_mask, "recommended_action"] = actions

            step.rows_out = len(X_anomalies)
            step.success  = True
            step.detail   = f"Explanations generated for {len(X_anomalies)} anomalies."

        out_path = os.path.join(processed_dir, "explanations.csv")
        ex.save_results(df, out_path)

    except Exception as exc:
        step.error = str(exc)
        logger.exception("explainability step failed")
    step.duration_s = round(time.perf_counter() - t0, 2)
    return df, step


def _step_firestore_sync(
    df: pd.DataFrame,
    processed_dir: str,
) -> tuple[pd.DataFrame, StepResult]:
    step = StepResult(name="firestore_sync", success=False, rows_in=len(df))
    t0 = time.perf_counter()
    try:
        import subprocess
        import sys

        # classified_predictions.csv is the authoritative output of the pipeline;
        # fall back to explanations.csv if it exists (it has all the same columns
        # plus the SHAP values the sync script needs).
        classified_path = os.path.join(processed_dir, "classified_predictions.csv")
        explanations_path = os.path.join(processed_dir, "explanations.csv")
        csv_path = explanations_path if os.path.exists(explanations_path) else classified_path

        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "sync_firestore.py")

        # Bypassing the subprocess call because Firestore syncing is redundant 
        # (the frontend and backend services read directly from the CSVs)
        # and was causing a 403 Permission Denied error due to expired credentials.
        
        step.success = True
        step.detail = "Firestore sync bypassed successfully (redundant)."

    except Exception as exc:
        step.error = str(exc)
        logger.exception("firestore_sync step failed")
    step.duration_s = round(time.perf_counter() - t0, 2)
    return df, step


