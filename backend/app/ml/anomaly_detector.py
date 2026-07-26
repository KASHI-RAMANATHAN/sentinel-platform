"""
Anomaly detection module using Isolation Forest.
Detects behavioral anomalies in access logs.
"""
import os
import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load the processed access logs data from a CSV file.
    
    Args:
        file_path (str): Path to the processed CSV file.
        
    Returns:
        pd.DataFrame: Loaded data.
    """
    logger.info(f"Loading data from: {file_path}")
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded {len(df)} records.")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

def select_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select numerical features relevant for anomaly detection.
    
    Args:
        df (pd.DataFrame): The input dataframe.
        
    Returns:
        pd.DataFrame: A dataframe containing only the selected features.
    """
    logger.info("Selecting features for anomaly detection...")
    
    # Selecting engineered numerical features that represent behavior
    features = [
        'login_hour',
        'day_of_week',
        'session_duration',
        'command_length',
        'unique_resources',
        'failed_login_count',
        'is_known_device',
        'is_known_location',
        'auth_method_encoded',
        'entity_type_encoded'
    ]
    
    # Only keep features that exist in the dataframe
    selected_features = [f for f in features if f in df.columns]
    logger.info(f"Selected {len(selected_features)} features: {selected_features}")
    
    return df[selected_features].copy()

def train_model(X: pd.DataFrame, contamination: float = 0.02) -> IsolationForest:
    """
    Train the Isolation Forest model on the selected features.
    
    Args:
        X (pd.DataFrame): The feature matrix.
        contamination (float): The expected proportion of anomalies in the dataset.
        
    Returns:
        IsolationForest: The trained model.
    """
    logger.info(f"Training Isolation Forest model with contamination={contamination}...")
    model = IsolationForest(
        n_estimators=100,
        max_samples='auto',
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X)
    logger.info("Model training completed.")
    return model

def predict_anomalies(model: IsolationForest, X: pd.DataFrame) -> np.ndarray:
    """
    Predict anomalies using the trained model.
    -1 = anomaly, 1 = normal
    
    Args:
        model (IsolationForest): The trained model.
        X (pd.DataFrame): The feature matrix.
        
    Returns:
        np.ndarray: Array of predictions.
    """
    logger.info("Predicting anomalies...")
    predictions = model.predict(X)
    return predictions

def calculate_anomaly_scores(model: IsolationForest, X: pd.DataFrame) -> np.ndarray:
    """
    Calculate anomaly scores using the trained model.
    Lower scores indicate more anomalous behavior.
    
    Args:
        model (IsolationForest): The trained model.
        X (pd.DataFrame): The feature matrix.
        
    Returns:
        np.ndarray: Array of anomaly scores.
    """
    logger.info("Calculating anomaly scores...")
    # The anomaly score of the input samples. The lower, the more abnormal.
    scores = model.decision_function(X)
    return scores

def save_predictions(df: pd.DataFrame, output_path: str):
    """
    Save the dataframe with appended predictions to a CSV file.
    
    Args:
        df (pd.DataFrame): The dataframe containing original data and predictions.
        output_path (str): The path to save the CSV file.
    """
    logger.info(f"Saving predictions to: {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Predictions saved successfully.")

def save_model(model: IsolationForest, output_path: str):
    """
    Persist the trained Isolation Forest model to disk.
    
    Args:
        model (IsolationForest): The trained model.
        output_path (str): The path to save the model.
    """
    logger.info(f"Saving model to: {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)
    logger.info("Model saved successfully.")

def main():
    # Define paths relative to the backend root directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    input_path = os.path.join(base_dir, 'data', 'processed', 'access_logs_processed.csv')
    predictions_path = os.path.join(base_dir, 'data', 'processed', 'predictions.csv')
    model_path = os.path.join(base_dir, 'app', 'ml', 'models', 'isolation_forest.pkl')
    
    try:
        # 1. Load data
        df = load_data(input_path)
        
        # 2. Select features
        X = select_features(df)
        
        # Fill any remaining NaNs just in case
        X = X.fillna(0)
        
        # 3. Train model
        model = train_model(X, contamination=0.02)
        
        # 4. Predict anomalies and calculate scores
        predictions = predict_anomalies(model, X)
        scores = calculate_anomaly_scores(model, X)
        
        # 5. Append predictions to the original dataframe
        df['anomaly_prediction'] = predictions
        df['anomaly_score'] = scores
        
        # 6. Save predictions
        save_predictions(df, predictions_path)
        
        # 7. Save model
        save_model(model, model_path)
        
        logger.info(f"Anomaly detection pipeline completed. Found {(predictions == -1).sum()} anomalies.")
        
    except Exception as e:
        logger.error(f"Anomaly detection pipeline failed: {e}")

if __name__ == "__main__":
    main()
