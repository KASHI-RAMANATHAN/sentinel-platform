import os
import sys
import uuid
import time
import logging
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("sync_firestore")

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.firebase.firestore_client import get_firestore_client

def sync_to_firestore(csv_path: str):
    if not os.path.exists(csv_path):
        logger.error(f"File not found: {csv_path}")
        raise FileNotFoundError(f"File not found: {csv_path}")
        
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        logger.error(f"Failed to read CSV: {exc}")
        raise exc

    # ── Normalise column names in case CSV still uses raw names ──────────
    # (handles both pre-renamed pipeline output and raw uploads)
    col_map = {
        "user_id":      "entity_id",
        "device_id":    "device_fingerprint",
        "ip":           "source_ip",
        "resource":     "resource_accessed",
        "login_method": "auth_method",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    if "geo_location" not in df.columns:
        if "city" in df.columns and "country" in df.columns:
            df["geo_location"] = df["city"].astype(str) + ", " + df["country"].astype(str)

    try:
        db = get_firestore_client()

        # ── Risk score: normalise using ANOMALY rows only (matches alert_service.py) ──
        anomaly_mask = df["anomaly_prediction"] == -1
        anomaly_scores = df.loc[anomaly_mask, "anomaly_score"]
        if len(anomaly_scores) == 0:
            logger.warning("No anomalies found in CSV — nothing to sync.")
            return

        min_score = float(anomaly_scores.min())
        max_score = float(anomaly_scores.max())

        def calc_risk(score):
            # Isolation Forest scores are negative → more negative = more anomalous.
            # We negate and normalise so higher risk = worse.
            negated = -float(score)
            n_min = -max_score
            n_max = -min_score
            if n_max == n_min:
                return 100.0
            risk = (negated - n_min) / (n_max - n_min) * 100.0
            return float(round(max(0.0, min(100.0, risk)), 2))

        def calc_severity(risk):
            if risk > 80: return "critical"
            if risk > 60: return "high"
            if risk > 30: return "medium"
            return "low"

        # Update devices
        devices_batch = db.batch()
        device_ops = 0
        device_col = "device_fingerprint" if "device_fingerprint" in df.columns else None
        if device_col:
            device_groups = df.groupby(device_col)
            for device_id, group in device_groups:
                if not device_id or str(device_id) == "nan":
                    continue
                
                safe_device_id = str(device_id).replace("/", "-").replace("\\", "-")
                
                last_row = group.sort_values("timestamp").iloc[-1]
                dev_ref = db.collection("devices").document(safe_device_id)
                devices_batch.set(dev_ref, {
                    "device_fingerprint": str(device_id),
                    "last_seen": str(last_row.get("timestamp", "")),
                    "entity_id": str(last_row.get("entity_id", "")),
                    "risk_score": calc_risk(float(last_row.get("anomaly_score", min_score))),
                    "status": "Monitored",
                    "geo_location": str(last_row.get("geo_location", "")),
                    "last_ip": str(last_row.get("source_ip", "")),
                }, merge=True)
                device_ops += 1
                if device_ops >= 400:
                    devices_batch.commit()
                    devices_batch = db.batch()
                    device_ops = 0
            if device_ops > 0:
                devices_batch.commit()

        # Update alerts
        alerts_batch = db.batch()
        alert_ops = 0
        anomaly_mask = df["anomaly_prediction"] == -1
        anomalies = df[anomaly_mask]
        
        for idx, row in anomalies.iterrows():
            alert_id = f"alert-{str(uuid.uuid4())[:8]}" # generate unique ID
            alert_ref = db.collection("alerts").document(alert_id)
            
            risk = calc_risk(float(row.get("anomaly_score", min_score)))
            raw_attack = str(row.get("predicted_attack_type", "Behavioral Anomaly"))
            
            # Simple SHAP parse
            shap_raw = row.get("shap_values", None)
            features = []
            if shap_raw and pd.notna(shap_raw):
                for part in str(shap_raw).split(","):
                    part = part.strip()
                    if ":" not in part:
                        continue
                    feat_name, val_str = part.split(":", 1)
                    try:
                        shap_val = float(val_str.strip())
                        features.append({"feature": feat_name.strip(), "shap_value": round(shap_val, 4), "description": feat_name.strip()})
                    except ValueError:
                        continue
                        
            summary = "High risk behavioral anomaly detected."
            if features:
                features.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
                top_factors = [f["feature"].lower() for f in features[:3]]
                if len(top_factors) > 1:
                    factors_str = ", ".join(top_factors[:-1]) + ", and " + top_factors[-1]
                else:
                    factors_str = top_factors[0]
                summary = f"High risk because the event exhibited abnormal {factors_str}."

            alerts_batch.set(alert_ref, {
                "alert_id": alert_id,
                "entity_id": str(row.get("entity_id", "")),
                "timestamp": str(row.get("timestamp", "")),
                "source_ip": str(row.get("source_ip", "")),
                "geo_location": str(row.get("geo_location", "")),
                "device_fingerprint": str(row.get("device_fingerprint", "")),
                "attack_type": raw_attack,
                "risk": risk,
                "risk_score": risk,
                "severity": calc_severity(risk),
                "status": "open",
                "ip": str(row.get("source_ip", "")),
                "user_id": str(row.get("entity_id", "")),
                "device_id": str(row.get("device_fingerprint", "")),
                "anomaly_score": float(row.get("anomaly_score", 0.0)),
                "recommendation": "Isolate entity and review access logs.",
                "shap_explanation": {
                    "top_features": features,
                    "summary": summary
                },
                "investigated_by": None,
                "investigated_at": None,
                "resolved_by": None,
                "resolved_at": None
            })
            alert_ops += 1
            if alert_ops >= 400:
                alerts_batch.commit()
                alerts_batch = db.batch()
                alert_ops = 0
        
        if alert_ops > 0:
            alerts_batch.commit()
            
        logger.info(f"Successfully synced {device_ops} devices and {len(anomalies)} alerts.")
        
    except Exception as exc:
        logger.error(f"Sync failed: {exc}")
        raise exc

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python sync_firestore.py <csv_path>")
        sys.exit(1)
    sync_to_firestore(sys.argv[1])
