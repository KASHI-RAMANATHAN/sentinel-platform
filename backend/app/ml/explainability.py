"""
app/ml/explainability.py

Fast rule-based explainability for Isolation Forest anomalies.

Why not SHAP?
-------------
SHAP's TreeExplainer and KernelExplainer both rely on C/C++ extensions that
crash or time out when called from a background thread on Windows
(the pattern uvicorn uses via asyncio.to_thread).  Rather than fight the
platform, we replace SHAP with a pure-Python, zero-crash alternative that
produces equivalent user-facing explanations:

  For each anomalous row we compute the z-score of every feature
  relative to the *normal* population.  Features with the largest
  absolute deviation from normal behaviour are ranked as the top
  contributors to the anomaly flag — exactly the information a SOC
  analyst needs, and exactly what SHAP was approximating anyway.

Output contract is identical to the previous SHAP-based module so
pipeline.py requires no changes to the call sites.
"""

import logging
import os
from typing import List, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel

from app.core.config import settings

# Attempt to import both Gemini and OpenAI (DeepSeek) clients
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature → human-readable description
# ---------------------------------------------------------------------------
_FEATURE_DESCRIPTIONS = {
    "login_hour":           "the login occurred outside the user's normal hours",
    "day_of_week":          "the login occurred on an unusual day of the week",
    "session_duration":     "the session duration was highly irregular",
    "command_length":       "unusual command activity was detected",
    "unique_resources":     "an unusual number of resources was accessed",
    "failed_login_count":   "there were multiple failed login attempts",
    "is_known_device":      "an unknown or unfamiliar device was used",
    "is_known_location":    "the login originated from an unfamiliar location",
    "auth_method_encoded":  "an unusual authentication method was employed",
    "entity_type_encoded":  "the entity behaviour deviated from normal baselines",
}


# ---------------------------------------------------------------------------
# Public API  (identical signatures to the old SHAP-based module)
# ---------------------------------------------------------------------------

def generate_shap_values(
    model,
    X: pd.DataFrame,
    background_sample_size: int = 50,
    X_full: pd.DataFrame = None,
):
    """
    Rule-based replacement for SHAP value generation.

    Computes per-feature z-scores of each anomalous row relative to the
    normal-population mean and standard deviation.  The resulting array
    has the same shape as SHAP's output (n_rows × n_features) and is
    consumed identically by identify_top_features / build_explanations.

    Args:
        model:                  Trained IsolationForest (unused — kept for
                                call-site compatibility).
        X:                      Feature DataFrame of anomalous rows.
        background_sample_size: Unused (kept for call-site compatibility).
        X_full:                 Full feature DataFrame used to calculate baseline normal statistics.

    Returns:
        (None, z_score_array)  — explainer is None; z_score_array is
        shape (len(X), n_features) with *negative* z-scores meaning the
        feature pushed the row toward anomaly, matching SHAP sign convention
        from the old TreeExplainer usage.
    """
    logger.info(
        "Computing rule-based feature scores for %d anomalous rows "
        "(fast, crash-free, no SHAP).",
        len(X),
    )

    if len(X) == 0:
        return None, np.zeros((0, len(X.columns)))

    X_arr = X.values.astype(float)

    # Use the full distribution of the provided rows as population stats.
    if X_full is not None and len(X_full) > 0:
        X_ref = X_full.values.astype(float)
    else:
        X_ref = X_arr
        
    col_mean = X_ref.mean(axis=0)
    col_std  = X_ref.std(axis=0)
    col_std  = np.where(col_std == 0, 1.0, col_std)   # avoid divide-by-zero

    z_scores = (X_arr - col_mean) / col_std

    # Negate: a row with a very *high* value (large positive z) is anomalous
    # in the same direction as a "negative SHAP" in tree explainer outputs.
    # Keeping it negative lets identify_top_features (argsort ascending) pick
    # the most-deviant features first without any changes to that function.
    return None, -np.abs(z_scores)


def identify_top_features(
    shap_values: np.ndarray,
    feature_names: List[str],
    top_n: int = 3,
) -> List[List[Tuple[str, float]]]:
    """
    Identify the top-N most anomalous features for each row.

    Works with both real SHAP values and the z-score array produced by
    generate_shap_values above — the sign convention is the same
    (more-negative = stronger contributor to anomaly).

    Returns:
        List of lists: for each row, a list of (feature_name, score) tuples
        ordered from most to least anomalous.
    """
    logger.info("Identifying top %d features for %d rows.", top_n, len(shap_values))

    top_features = []
    for i in range(len(shap_values)):
        instance = shap_values[i]
        sorted_idx = np.argsort(instance)          # most-negative first
        top_idx = sorted_idx[:top_n]

        row_top = [
            (feature_names[idx], float(instance[idx]))
            for idx in top_idx
            if instance[idx] < 0
        ]
        top_features.append(row_top)

    return top_features


class AnomalyExplanation(BaseModel):
    id: str
    explanation: str
    recommended_action: str

class ExplanationResponse(BaseModel):
    explanations: list[AnomalyExplanation]

def _build_rule_based_explanations(
    top_features_list: List[List[Tuple[str, float]]],
) -> Tuple[List[str], List[str]]:
    """Fallback rule-based explanations."""
    explanations = []
    actions = []
    for top_features in top_features_list:
        if not top_features:
            explanations.append("Low risk: Activity aligns with normal baseline behaviour.")
            actions.append("No action required.")
            continue

        reasons = [
            _FEATURE_DESCRIPTIONS.get(fname, f"unusual behaviour in {fname}")
            for fname, _ in top_features
        ]

        if len(reasons) == 1:
            explanation = f"High risk because {reasons[0]}."
        elif len(reasons) == 2:
            explanation = f"High risk because {reasons[0]} and {reasons[1]}."
        else:
            explanation = (
                f"High risk because {reasons[0]}, {reasons[1]}, "
                f"and {reasons[2]}."
            )
        explanations.append(explanation)
        actions.append("Investigate the session and enforce MFA if necessary.")

    return explanations, actions

def build_explanations(
    top_features_list: List[List[Tuple[str, float]]],
) -> Tuple[List[str], List[str]]:
    """
    Build natural-language explanations and recommended actions.
    Uses Gemini Pro if available, falling back to rules.
    Only processes up to 50 anomalies to respect API limits.
    """
    logger.info("Building explanations for %d rows.", len(top_features_list))

    # Choose AI provider based on available API keys
    if settings.GEMINI_API_KEY and genai:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as exc:
            logger.warning("Failed to initialize Gemini client: %s. Falling back to rules.", exc)
            client = None
    elif settings.DEEPSEEK_API_KEY and OpenAI:
        try:
            client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
        except Exception as exc:
            logger.warning("Failed to initialize DeepSeek client: %s. Falling back to rules.", exc)
            client = None
    else:
        client = None

    if not client:
        logger.info("No AI client available. Falling back to rule-based engine.")
        return _build_rule_based_explanations(top_features_list)
        
    cap = min(len(top_features_list), 50)
    batch = top_features_list[:cap]
    
    # Prepare batch for prompt
    anomalies_json = []
    for idx, features in enumerate(batch):
        anomalies_json.append({
            "id": str(idx),
            "features": [{"name": f, "z_score": float(s)} for f, s in features]
        })

    prompt = (
        "You are an expert SOC analyst AI. "
        "I have a list of anomalous network sessions. "
        "For each anomaly, you will receive its 'id' and the top contributing features that caused it to be flagged (along with their z-scores relative to normal). "
        "Your task is to analyze these features and output a precise, human-readable 'explanation' and a clear, actionable 'recommended_action' for each. "
        "You must respond in valid JSON format. The JSON should be an object containing a list 'explanations', where each element has 'id', 'explanation', and 'recommended_action'.\n\n"
        f"Anomalies:\n{anomalies_json}"
    )

    explanations_out = []
    actions_out = []
    
    try:
        logger.info("Calling AI to analyze %d anomalies...", cap)
        if settings.GEMINI_API_KEY and genai:
            # Try models in order until one succeeds
            _GEMINI_MODELS = [
                'models/gemini-flash-lite-latest',
                'models/gemini-2.0-flash',
                'models/gemini-2.5-flash',
            ]
            response = None
            for _model in _GEMINI_MODELS:
                try:
                    response = client.models.generate_content(
                        model=_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=ExplanationResponse,
                        ),
                    )
                    logger.info("Used Gemini model: %s", _model)
                    break
                except Exception as _e:
                    logger.warning("Model %s failed (%s), trying next...", _model, str(_e)[:80])
            # Parse Gemini structured response
            structured_data = (response.parsed if response and response.parsed else None)
        else:
            # DeepSeek call – expects JSON response
            response = client.chat.completions.create(
                model='deepseek-chat',
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            import json
            structured_data = json.loads(response.choices[0].message.content)
        
        if not structured_data:
            logger.warning("AI service did not return valid structured data. Falling back to rules.")
            return _build_rule_based_explanations(top_features_list)

        # Normalise the structure for both providers
        if settings.GEMINI_API_KEY and genai:
            # Gemini provides objects with attribute access
            gen_map = {item.id: item for item in structured_data.explanations}
            get_explanation = lambda itm: itm.explanation
            get_action = lambda itm: itm.recommended_action
        else:
            # DeepSeek returns dicts
            gen_map = {str(item["id"]): item for item in structured_data["explanations"]}
            get_explanation = lambda itm: itm.get("explanation", "")
            get_action = lambda itm: itm.get("recommended_action", "")

        for idx in range(len(top_features_list)):
            str_id = str(idx)
            if str_id in gen_map:
                explanations_out.append(get_explanation(gen_map[str_id]))
                actions_out.append(get_action(gen_map[str_id]))
            else:
                # Fallback for missing/capped ones
                rules_exp, rules_act = _build_rule_based_explanations([top_features_list[idx]])
                explanations_out.extend(rules_exp)
                actions_out.extend(rules_act)

        logger.info("AI explanation generation successful.")
        return explanations_out, actions_out
            
    except Exception as exc:
        logger.error("AI API call failed: %s. Falling back to rules.", exc)
        return _build_rule_based_explanations(top_features_list)


def save_results(df: pd.DataFrame, output_path: str) -> None:
    """Save the final DataFrame with explanation columns."""
    logger.info("Saving explanations → %s", output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Explanations saved.")


# ---------------------------------------------------------------------------
# Standalone entry-point (legacy support)
# ---------------------------------------------------------------------------

def load_model(model_path: str):
    """Load a joblib model (kept for backward compatibility)."""
    import joblib
    logger.info("Loading model from: %s", model_path)
    return joblib.load(model_path)


def load_data(file_path: str) -> pd.DataFrame:
    """Load a CSV (kept for backward compatibility)."""
    logger.info("Loading data from: %s", file_path)
    df = pd.read_csv(file_path)
    logger.info("Loaded %d records.", len(df))
    return df


def main() -> None:
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    input_path  = os.path.join(base_dir, "data", "processed", "classified_predictions.csv")
    output_path = os.path.join(base_dir, "data", "processed", "explanations.csv")
    model_path  = os.path.join(base_dir, "app", "ml", "models", "isolation_forest.pkl")

    try:
        df = load_data(input_path)
        model = load_model(model_path)

        features = [
            "login_hour", "day_of_week", "session_duration", "command_length",
            "unique_resources", "failed_login_count", "is_known_device",
            "is_known_location", "auth_method_encoded", "entity_type_encoded",
        ]
        selected = [f for f in features if f in df.columns]
        X = df[selected].fillna(0)

        anomaly_mask = df["anomaly_prediction"] == -1
        X_anomalies  = X[anomaly_mask]

        df["top_features"] = None
        df["shap_values"]  = None
        df["explanation"]  = "Normal activity."
        df["recommended_action"] = "No action required."

        if len(X_anomalies) > 0:
            _, scores         = generate_shap_values(model, X_anomalies, X_full=X)
            top_features_list = identify_top_features(scores, selected, top_n=3)
            explanations, actions = build_explanations(top_features_list)

            formatted_top  = [", ".join(f for f, _ in tf) for tf in top_features_list]
            formatted_vals = [", ".join(f"{f}: {s:.4f}" for f, s in tf) for tf in top_features_list]

            df.loc[anomaly_mask, "top_features"] = formatted_top
            df.loc[anomaly_mask, "shap_values"]  = formatted_vals
            df.loc[anomaly_mask, "explanation"]  = explanations
            df.loc[anomaly_mask, "recommended_action"] = actions

        save_results(df, output_path)
        logger.info("Explainability pipeline completed.")

    except Exception as exc:
        logger.error("Explainability pipeline failed: %s", exc)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
