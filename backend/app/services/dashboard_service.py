"""
app/services/dashboard_service.py

Business logic for aggregate dashboard statistics.

Reads the ML pipeline output (classified_predictions.csv) and computes:
  - total_sessions          : total rows in the dataset
  - active_threats          : rows where anomaly_prediction == -1
  - average_risk_score      : mean anomaly_score (Isolation Forest decision function)
  - devices_monitored       : count of unique device_id values
  - top_attack_types        : top-5 predicted attack types (threats only)
  - severity_breakdown      : threats bucketed into Low/Medium/High/Critical bands
"""

import logging
import os
from collections import Counter
from functools import lru_cache

import pandas as pd
from google.cloud.firestore_v1 import Client as FirestoreClient
from typing import Optional

from app.schemas.dashboard_schema import DashboardStatsResponse, SeverityBreakdown

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column names produced by the ML pipeline
# ---------------------------------------------------------------------------
_COL_ANOMALY_PRED = "anomaly_prediction"   # -1 = anomaly, 1 = normal
_COL_ANOMALY_SCORE = "anomaly_score"        # IsolationForest decision_function score
_COL_DEVICE_ID = "device_fingerprint"
_COL_ATTACK_TYPE = "predicted_attack_type"

# Isolation Forest score boundaries for severity bucketing are replaced by mapping risk scores.
def _score_to_severity(score: float, score_min: float, score_max: float) -> str:
    """Map an Isolation Forest anomaly score to a severity label via risk_score."""
    if score_max == score_min:
        risk = 100.0
    else:
        negated = -score
        n_min = -score_max
        n_max = -score_min
        risk = (negated - n_min) / (n_max - n_min) * 100.0

    if risk > 80.0:
        return "critical"
    if risk > 60.0:
        return "high"
    if risk > 30.0:
        return "medium"
    return "low"


class DashboardService:
    """Encapsulates business logic for computing dashboard statistics from CSV data."""

    def __init__(self, data_dir: str, db: Optional[FirestoreClient] = None) -> None:
        """
        Args:
            data_dir: Absolute (or CWD-relative) path to the processed data
                      directory that contains classified_predictions.csv.
        """
        self._csv_path = os.path.join(data_dir, "classified_predictions.csv")
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_stats(self) -> DashboardStatsResponse:
        """
        Load the classified predictions CSV and compute dashboard KPIs.

        Returns a fully-populated DashboardStatsResponse. If the CSV is
        unavailable (pipeline not yet run), returns a zeroed-out response
        with a warning log rather than raising an HTTP 500.
        """
        df = self._load_csv()
        if df is None:
            logger.warning(
                "classified_predictions.csv not found at %s — "
                "returning empty dashboard stats.",
                self._csv_path,
            )
            return DashboardStatsResponse()

        return self._compute_stats(df)

    async def get_trends(self) -> dict:
        """
        Compute anomaly trends over time.
        Groups data by 1-hour intervals for the last 24 hours.
        """
        df = self._load_csv()
        
        def empty_response():
            return {
                "labels": [f"{i:02d}:00" for i in range(24)],
                "normal": [0]*24,
                "anomaly": [0]*24
            }

        if df is None or len(df) == 0:
            return empty_response()
        
        if "timestamp" not in df.columns:
            return empty_response()
            
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df.set_index("timestamp", inplace=True)
        
        resampled = df.groupby(pd.Grouper(freq="1h"))
        
        labels = []
        normal_counts = []
        anomaly_counts = []
        
        for time_idx, group in resampled:
            total = len(group)
            anomalies = int((group[_COL_ANOMALY_PRED] == -1).sum()) if _COL_ANOMALY_PRED in group.columns else 0
            normal = total - anomalies
            labels.append(time_idx.strftime("%H:%M"))
            normal_counts.append(normal)
            anomaly_counts.append(anomalies)
        
        if not labels:
            return empty_response()

        # Return last 24 intervals (24 hours)
        return {
            "labels": labels[-24:],
            "normal": normal_counts[-24:],
            "anomaly": anomaly_counts[-24:]
        }

    async def get_distribution(self) -> dict:
        """
        Compute the distribution of attack types dynamically.
        """
        df = self._load_csv()
        if df is None or len(df) == 0 or _COL_ATTACK_TYPE not in df.columns or _COL_ANOMALY_PRED not in df.columns:
            return {"labels": ["Behavioral Anomaly"], "values": [0]}
            
        threat_mask = df[_COL_ANOMALY_PRED] == -1
        threat_df = df[threat_mask]
        total_anomalies = len(threat_df)
        
        if total_anomalies == 0:
            return {"labels": ["Behavioral Anomaly"], "values": [0]}
            
        # Do not restrict to VALID_ATTACK_TYPES; use all found in the predictions
        counts = Counter(threat_df[_COL_ATTACK_TYPE].dropna())
        
        labels = []
        values = []
        for atype, count in counts.most_common():
            pct = round((count / total_anomalies) * 100)
            labels.append(atype)
            values.append(pct)
            
        return {"labels": labels, "values": values}

    async def get_network_traffic(self) -> dict:
        """
        Compute network traffic based on session_duration (ingress proxy) 
        and command_length (egress proxy) over the last 24 intervals.
        """
        df = self._load_csv()
        
        def empty_response():
            return {
                "labels": [f"{i:02d}:00" for i in range(24)],
                "ingress": [0]*24,
                "egress": [0]*24
            }
            
        if df is None or len(df) == 0:
            return empty_response()
            
        if "timestamp" not in df.columns:
            return empty_response()
            
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df.set_index("timestamp", inplace=True)
        
        resampled = df.groupby(pd.Grouper(freq="1h"))
        
        labels = []
        ingress = []
        egress = []
        
        has_session = "session_duration" in df.columns
        has_command = "command_length" in df.columns
        
        for time_idx, group in resampled:
            labels.append(time_idx.strftime("%H:%M"))
            
            # Using session_duration as a proxy for ingress bytes (multiply to make it look like MBs)
            i_val = float(group["session_duration"].sum()) * 1.5 if has_session else 0.0
            ingress.append(int(i_val))
            
            # Using command_length as a proxy for egress bytes
            e_val = float(group["command_length"].sum()) * 5.0 if has_command else 0.0
            egress.append(int(e_val))
            
        if not labels:
            return empty_response()
            
        return {
            "labels": labels[-24:],
            "ingress": ingress[-24:],
            "egress": egress[-24:]
        }

    async def get_connection_protocols(self) -> dict:
        """
        Compute top connection protocols (auth_method).
        """
        df = self._load_csv()
        if df is None or len(df) == 0:
            return {"protocols": []}
            
        # Try to use 'auth_method' if available, otherwise fallback to 'auth_method_encoded'
        col_name = "auth_method"
        if col_name not in df.columns:
            if "auth_method_encoded" in df.columns:
                col_name = "auth_method_encoded"
            else:
                return {"protocols": []}
                
        counts = Counter(df[col_name].dropna())
        
        protocols = []
        for name, count in counts.most_common(10):
            protocols.append({
                "name": str(name).upper(),
                "count": int(count)
            })
            
        return {"protocols": protocols}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_csv(self) -> pd.DataFrame | None:
        """Load the predictions CSV; return None if the file is missing."""
        if not os.path.exists(self._csv_path):
            return None
        try:
            df = pd.read_csv(self._csv_path)
            logger.info("Loaded %d rows from %s", len(df), self._csv_path)
            return df
        except Exception as exc:
            logger.error("Failed to read %s: %s", self._csv_path, exc)
            return None

    def _compute_stats(self, df: pd.DataFrame) -> DashboardStatsResponse:
        """Derive all KPIs from the loaded DataFrame."""

        # ── Core metrics ──────────────────────────────────────────────
        total_sessions: int = len(df)

        # anomaly_prediction == -1 means the Isolation Forest flagged a threat
        threat_mask = (
            df[_COL_ANOMALY_PRED] == -1
            if _COL_ANOMALY_PRED in df.columns
            else pd.Series([False] * total_sessions)
        )
        
        # ── Fetch Overrides from Firestore ────────────────────────────
        resolved_indices = set()
        if self._db is not None:
            try:
                docs = self._db.collection("alerts").where("status", "==", "resolved").stream()
                resolved_ids = {doc.id for doc in docs}
                
                # If dataframe has an explicit alert ID (like entity_id or custom logic)
                # Currently the frontend gets alert IDs as "alert-NNNNNN" where NNNNNN is the padded dataframe index.
                # Let's map "alert-NNNNNN" back to the row index to turn off the threat mask
                for r_id in resolved_ids:
                    if r_id.startswith("alert-"):
                        try:
                            idx = int(r_id.split("-")[1])
                            resolved_indices.add(idx)
                        except ValueError:
                            pass
            except Exception as exc:
                logger.error("Failed to fetch overrides from Firestore in dashboard: %s", exc)
                
        # Exclude resolved alerts from the threat mask
        if resolved_indices:
            # We must only update indices that actually exist in the mask
            valid_indices = [idx for idx in resolved_indices if idx in threat_mask.index]
            threat_mask.loc[valid_indices] = False

        active_threats: int = int(threat_mask.sum())

        # Average risk score across *all* threats.
        if _COL_ANOMALY_SCORE in df.columns and active_threats > 0:
            threat_scores = df.loc[threat_mask, _COL_ANOMALY_SCORE]
            s_min, s_max = float(threat_scores.min()), float(threat_scores.max())
            
            if s_max == s_min:
                average_risk_score = 100.0
            else:
                raw_avg = float(threat_scores.mean())
                negated = -raw_avg
                n_min = -s_max
                n_max = -s_min
                risk = (negated - n_min) / (n_max - n_min) * 100.0
                average_risk_score = float(max(0.0, min(100.0, round(risk, 0))))
        else:
            average_risk_score = 0.0

        devices_monitored: int = (
            int(df[_COL_DEVICE_ID].nunique())
            if _COL_DEVICE_ID in df.columns
            else 0
        )

        # ── Top attack types (threats only) ───────────────────────────
        top_attack_types = None
        if _COL_ATTACK_TYPE in df.columns and active_threats > 0:
            threat_df = df[threat_mask]
            counts: Counter = Counter(threat_df[_COL_ATTACK_TYPE].dropna())
            top_attack_types = [
                {"attack_type": atype, "count": cnt}
                for atype, cnt in counts.most_common(5)
            ]

        # ── Severity breakdown (threats only) ─────────────────────────
        severity = SeverityBreakdown()
        if _COL_ANOMALY_SCORE in df.columns and active_threats > 0:
            threat_scores = df.loc[threat_mask, _COL_ANOMALY_SCORE]
            s_min, s_max = float(threat_scores.min()), float(threat_scores.max())
            sev_counts: Counter = Counter(threat_scores.apply(lambda x: _score_to_severity(x, s_min, s_max)))
            severity = SeverityBreakdown(
                low=sev_counts.get("low", 0),
                medium=sev_counts.get("medium", 0),
                high=sev_counts.get("high", 0),
                critical=sev_counts.get("critical", 0),
            )

        return DashboardStatsResponse(
            total_sessions=total_sessions,
            active_threats=active_threats,
            average_risk_score=average_risk_score,
            devices_monitored=devices_monitored,
            total_logs_ingested=total_sessions,
            top_attack_types=top_attack_types,
            severity_breakdown=severity,
        )
