import logging
from app.ml.inference_engine import InferenceEngine

logging.basicConfig(level=logging.INFO)

def test_inference():
    model_dir = "app/ml/models"
    engine = InferenceEngine.get_instance(model_dir)
    
    # Missing auth_method_encoded and entity_type_encoded previously caused crash.
    feature_vector = {
        "login_hour": 3,
        "day_of_week": 6,
        "session_duration": 400.5,
        "command_length": 50,
        "unique_resources": 10,
        "failed_login_count": 5,
        "is_known_device": 0,
        "is_known_location": 0,
        "auth_method_encoded": 1,
        "entity_type_encoded": 2,
    }
    
    try:
        result = engine.predict(feature_vector)
        print("INFERENCE SUCCESS!")
        print(f"Is Anomaly: {result.is_anomaly}")
        print(f"Risk Score: {result.risk_score}")
        print(f"Attack: {result.predicted_attack}")
        print(f"Confidence: {result.confidence}")
    except Exception as e:
        print(f"INFERENCE FAILED: {e}")

if __name__ == "__main__":
    test_inference()
