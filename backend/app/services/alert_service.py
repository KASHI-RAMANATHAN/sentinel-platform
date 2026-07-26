"""
app/services/alert_service.py

Business logic for anomaly alerts.
"""

import logging
import math
import os
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import pandas as pd
from fastapi import HTTPException
from google.cloud.firestore_v1 import Client as FirestoreClient

from app.schemas.alert_schema import (
    AlertDetail,
    AlertItem,
    AlertSeverity,
    AlertStatus,
    PaginatedAlertResponse,
    ShapExplanation,
    ShapFeature,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column name constants (matches classified_predictions.csv)
# ---------------------------------------------------------------------------
_COL_ANOMALY_PRED = "anomaly_prediction"
_COL_ANOMALY_SCORE = "anomaly_score"
_COL_ATTACK_TYPE = "predicted_attack_type"
_COL_TIMESTAMP = "timestamp"
_COL_ENTITY_ID = "entity_id"
_COL_DEVICE_FINGERPRINT = "device_fingerprint"
_COL_SOURCE_IP = "source_ip"

# ---------------------------------------------------------------------------
# Severity thresholds (applied to normalised 0-100 risk score)
# ---------------------------------------------------------------------------
_SEVERITY_CRITICAL = 80.0
_SEVERITY_HIGH = 60.0
_SEVERITY_MEDIUM = 30.0



def _risk_to_severity(risk: float) -> AlertSeverity:
    if risk > _SEVERITY_CRITICAL:
        return AlertSeverity.CRITICAL
    if risk > _SEVERITY_HIGH:
        return AlertSeverity.HIGH
    if risk > _SEVERITY_MEDIUM:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def _normalise_scores(scores: pd.Series) -> pd.Series:
    s_min, s_max = scores.min(), scores.max()
    if s_max == s_min:
        return pd.Series([100.0] * len(scores), index=scores.index)
    negated = -scores
    n_min, n_max = negated.min(), negated.max()
    normalised = (negated - n_min) / (n_max - n_min) * 100.0
    return normalised.round(0)


class AlertService:
    """Reads classified_predictions.csv / explanations.csv and returns alert records."""

    def __init__(self, data_dir: str, db: Optional[FirestoreClient] = None) -> None:
        self._csv_path = os.path.join(data_dir, "classified_predictions.csv")
        self._expl_path = os.path.join(data_dir, "explanations.csv")
        self._db = db
        # We now cache the BASE alerts from the CSV, but we apply Firestore 
        # overrides dynamically so they don't get permanently stuck in cache.
        self._base_alerts_cache: Optional[List[AlertItem]] = None
        self._score_min: Optional[float] = None
        self._score_max: Optional[float] = None

    async def list_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        status_filter: Optional[AlertStatus] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedAlertResponse:
        all_alerts = await self._get_all_alerts()

        filtered = all_alerts
        if severity is not None:
            filtered = [a for a in filtered if a.severity == severity]
        if status_filter is not None:
            filtered = [a for a in filtered if a.status == status_filter]

        total = len(filtered)
        total_pages = max(1, math.ceil(total / page_size))
        page = max(1, min(page, total_pages))

        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        return PaginatedAlertResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            alerts=page_items,
        )

    async def _get_all_alerts(self) -> List[AlertItem]:
        # 1. Get base alerts from CSV (using cache if available)
        if self._base_alerts_cache is None:
            df = self._load_threats()
            if df is None or df.empty:
                self._base_alerts_cache = []
            else:
                self._base_alerts_cache = self._build_alert_items(df)

        base_alerts = [a.model_copy() for a in self._base_alerts_cache]

        # 2. Fetch overrides from Firestore
        overrides = {}
        if self._db is not None:
            try:
                # In a real app we'd want to paginate or filter this, 
                # but for the demo we'll fetch all overrides.
                docs = self._db.collection("alerts").stream()
                for doc in docs:
                    overrides[doc.id] = doc.to_dict()
            except Exception as exc:
                logger.error("Failed to fetch overrides from Firestore: %s", exc)

        # 3. Apply overrides
        for alert in base_alerts:
            if alert.id in overrides:
                override = overrides[alert.id]
                if "status" in override:
                    try:
                        alert.status = AlertStatus(override["status"])
                    except ValueError:
                        pass
                if "severity" in override:
                    try:
                        alert.severity = AlertSeverity(override["severity"])
                    except ValueError:
                        pass
                if "risk_score" in override:
                    alert.risk_score = int(override["risk_score"])
        
        # Sort again by risk since overrides might have changed it
        base_alerts.sort(key=lambda a: a.risk_score, reverse=True)
        return base_alerts

    def _load_threats(self) -> Optional[pd.DataFrame]:
        if not os.path.exists(self._csv_path):
            logger.warning("CSV not found at %s — returning empty alert list.", self._csv_path)
            return None
        try:
            df = pd.read_csv(self._csv_path)
        except Exception as exc:
            logger.error("Failed to read %s: %s", self._csv_path, exc)
            return None

        if _COL_ANOMALY_PRED not in df.columns:
            return None

        threats = df[df[_COL_ANOMALY_PRED] == -1].copy().reset_index(drop=False)
        return threats

    def _build_alert_items(self, df: pd.DataFrame) -> List[AlertItem]:
        if _COL_ANOMALY_SCORE in df.columns:
            df["_risk_score"] = _normalise_scores(df[_COL_ANOMALY_SCORE])
        else:
            df["_risk_score"] = 50.0

        df = df.sort_values("_risk_score", ascending=False).reset_index(drop=True)
        df["_severity"] = df["_risk_score"].map(_risk_to_severity)

        if _COL_ATTACK_TYPE in df.columns:
            df["_attack_type"] = df.apply(self._infer_attack_type_row, axis=1)
        else:
            df["_attack_type"] = df.apply(self._infer_attack_type_row, axis=1)

        if _COL_TIMESTAMP in df.columns:
            df["_timestamp"] = pd.to_datetime(df[_COL_TIMESTAMP], errors="coerce")
            df["_timestamp"] = df["_timestamp"].fillna(datetime.utcnow())
        else:
            df["_timestamp"] = datetime.utcnow()

        items: List[AlertItem] = []
        for pos, row in df.iterrows():
            orig_idx = int(row["index"]) if "index" in row.index else int(pos)
            items.append(
                AlertItem(
                    id=f"alert-{orig_idx:06d}",
                    risk_score=int(row["_risk_score"]),
                    severity=row["_severity"],
                    attack_type=str(row["_attack_type"]),
                    status=AlertStatus.OPEN,
                    timestamp=row["_timestamp"].to_pydatetime()
                    if hasattr(row["_timestamp"], "to_pydatetime")
                    else row["_timestamp"],
                    entity_id=str(row[_COL_ENTITY_ID]) if _COL_ENTITY_ID in row.index and pd.notna(row[_COL_ENTITY_ID]) else None,
                    device_fingerprint=str(row[_COL_DEVICE_FINGERPRINT]) if _COL_DEVICE_FINGERPRINT in row.index and pd.notna(row[_COL_DEVICE_FINGERPRINT]) else None,
                    source_ip=str(row[_COL_SOURCE_IP]) if _COL_SOURCE_IP in row.index and pd.notna(row[_COL_SOURCE_IP]) else None,
                    anomaly_score=float(row[_COL_ANOMALY_SCORE]) if _COL_ANOMALY_SCORE in row.index else 0.0,
                )
            )

        return items

    async def get_alert_by_id(self, alert_id: str) -> AlertDetail:
        row_index = self._parse_alert_id(alert_id)
        df = self._load_full_dataset()
        if df is None:
            raise HTTPException(status_code=503, detail="Prediction dataset unavailable.")

        if row_index >= len(df) or row_index < 0:
            raise HTTPException(status_code=404, detail="Alert not found")

        row = df.iloc[row_index]

        if int(row.get(_COL_ANOMALY_PRED, 1)) != -1:
            raise HTTPException(
                status_code=404,
                detail=f"Row {row_index} is not flagged as a threat; no alert exists.",
            )

        return self._build_alert_detail(alert_id, row, df)

    @staticmethod
    def _parse_alert_id(alert_id: str) -> int:
        prefix = "alert-"
        if not alert_id.startswith(prefix):
            raise HTTPException(
                status_code=404,
                detail="Alert not found",
            )
        try:
            return int(alert_id[len(prefix):])
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail="Alert not found",
            )

    def _load_full_dataset(self) -> Optional[pd.DataFrame]:
        path = self._expl_path if os.path.exists(self._expl_path) else self._csv_path
        if not os.path.exists(path):
            return None
        try:
            df = pd.read_csv(path)
            return df
        except Exception as exc:
            return None

    def _build_alert_detail(
        self, alert_id: str, row: pd.Series, df: pd.DataFrame
    ) -> AlertDetail:
        anomaly_score = float(row.get(_COL_ANOMALY_SCORE, 0.0))
        risk_score = int(self._single_row_risk(anomaly_score, df))

        raw_attack = str(row.get(_COL_ATTACK_TYPE, "")) if _COL_ATTACK_TYPE in row.index else ""
        attack_type = raw_attack if raw_attack and raw_attack != "nan" and raw_attack.lower() != "unknown" else self._infer_attack_type_row(row)

        ts_raw = row.get(_COL_TIMESTAMP)
        try:
            timestamp = pd.to_datetime(ts_raw).to_pydatetime()
        except Exception:
            timestamp = datetime.utcnow()

        shap_explanation = self._parse_shap(row)

        return AlertDetail(
            id=alert_id,
            timestamp=timestamp,
            entity_id=str(row["entity_id"]) if "entity_id" in row.index and pd.notna(row["entity_id"]) else None,
            entity_type=str(row["entity_type"]) if "entity_type" in row.index and pd.notna(row["entity_type"]) else None,
            source_ip=str(row["source_ip"]) if "source_ip" in row.index and pd.notna(row["source_ip"]) else None,
            geo_location=str(row["geo_location"]) if "geo_location" in row.index and pd.notna(row["geo_location"]) else None,
            device_fingerprint=str(row["device_fingerprint"]) if "device_fingerprint" in row.index and pd.notna(row["device_fingerprint"]) else None,
            resource_accessed=str(row["resource_accessed"]) if "resource_accessed" in row.index and pd.notna(row["resource_accessed"]) else None,
            auth_method=str(row["auth_method"]) if "auth_method" in row.index and pd.notna(row["auth_method"]) else None,
            session_duration=float(row["session_duration"]) if "session_duration" in row.index and pd.notna(row["session_duration"]) else None,
            command_sequence=str(row["command_sequence"]) if "command_sequence" in row.index and pd.notna(row["command_sequence"]) else None,
            login_success=bool(row["login_success"]) if "login_success" in row.index and pd.notna(row["login_success"]) else None,
            label=str(row["label"]) if "label" in row.index and pd.notna(row["label"]) else None,
            risk_score=risk_score,
            anomaly_score=anomaly_score,
            prediction=int(row.get("anomaly_prediction", -1)),
            attack_type=attack_type,
            shap_explanation=shap_explanation,
            recommended_action=str(row["recommended_action"]) if "recommended_action" in row.index and pd.notna(row["recommended_action"]) else None
        )

    def _single_row_risk(self, anomaly_score: float, df: pd.DataFrame) -> float:
        if self._score_min is None or self._score_max is None:
            if _COL_ANOMALY_SCORE in df.columns and _COL_ANOMALY_PRED in df.columns:
                threat_scores = df.loc[df[_COL_ANOMALY_PRED] == -1, _COL_ANOMALY_SCORE]
                self._score_min = float(threat_scores.min())
                self._score_max = float(threat_scores.max())
            else:
                return 50.0

        s_min, s_max = self._score_min, self._score_max
        if s_max == s_min:
            return 100.0

        negated = -anomaly_score
        n_min = -s_max
        n_max = -s_min
        risk = (negated - n_min) / (n_max - n_min) * 100.0
        return round(max(0.0, min(100.0, risk)), 0)

    @staticmethod
    def _parse_shap(row: pd.Series, explanation_override: str = None) -> ShapExplanation:
        _FEAT_DESC: Dict[str, str] = {
            "login_hour":          "Time of Day",
            "day_of_week":         "Day of Week",
            "session_duration":    "Session Duration",
            "command_length":      "Command Length",
            "unique_resources":    "Resource Access Count",
            "failed_login_count":  "Failed Login Count",
            "is_known_device":     "Device Fingerprint",
            "is_known_location":   "Geo Location",
            "auth_method_encoded": "Authentication Method",
            "entity_type_encoded": "Entity Type",
            "command_sequence":    "Command Sequence",
            "login_success":       "Login Success",
        }

        shap_raw = row.get("shap_values", None)

        features: List[ShapFeature] = []
        if shap_raw and pd.notna(shap_raw):
            for part in str(shap_raw).split(","):
                part = part.strip()
                if ":" not in part:
                    continue
                feat_name, val_str = part.split(":", 1)
                feat_name = feat_name.strip()
                try:
                    shap_val = float(val_str.strip())
                except ValueError:
                    continue
                features.append(
                    ShapFeature(
                        feature=_FEAT_DESC.get(feat_name, feat_name),
                        shap_value=round(shap_val, 4),
                        description=_FEAT_DESC.get(feat_name, feat_name),
                    )
                )

        # Sort features by highest impact (absolute value)
        features.sort(key=lambda x: abs(x.shap_value), reverse=True)
        
        # Use the AI/rule-based explanation from the CSV if available, otherwise build from features
        csv_explanation = explanation_override or (
            str(row.get("explanation", "")) if "explanation" in row.index and pd.notna(row.get("explanation")) else ""
        )
        if csv_explanation and csv_explanation not in ("", "nan", "Normal activity.", "None"):
            summary = csv_explanation
        else:
            summary = "High risk behavioral anomaly detected."
            if features:
                top_factors = [f.feature.lower() for f in features[:3]]
                if len(top_factors) > 1:
                    factors_str = ", ".join(top_factors[:-1]) + ", and " + top_factors[-1]
                else:
                    factors_str = top_factors[0]
                summary = f"High risk because the event exhibited abnormal {factors_str}."

        return ShapExplanation(top_features=features, summary=summary)

    def _infer_attack_type_row(self, row: pd.Series) -> str:
        # Default fallback
        inferred = "Behavioral Anomaly"
        
        raw = str(row.get(_COL_ATTACK_TYPE, "")) if _COL_ATTACK_TYPE in row.index else ""
        if raw and raw != "nan" and raw.lower() != "unknown":
            return raw

        # Rule-based inference
        login_success = row.get("login_success", None)
        auth_method = str(row.get("auth_method", "")).upper()
        session_duration = row.get("session_duration", 0)
        command_seq = str(row.get("command_sequence", ""))

        if login_success is False or login_success == 0 or login_success == "False":
            inferred = "Credential Abuse"
        elif "VPN" in auth_method:
            inferred = "Impossible Travel"
        elif pd.notna(session_duration) and float(session_duration) > 5000:
            inferred = "Session Hijacking"
        elif command_seq and command_seq.lower() != "nan" and command_seq.lower() != "unknown":
            inferred = "Insider Threat"
            
        return inferred
