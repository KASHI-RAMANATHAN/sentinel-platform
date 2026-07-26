import pandas as pd
import numpy as np
import os
import logging
from sklearn.preprocessing import LabelEncoder

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load the raw access logs data from a CSV file.
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

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataset by handling missing values and ensuring correct data types.
    """
    logger.info("Cleaning data...")
    df = df.copy()
    
    # Define categorical columns to fill missing values
    cat_cols = ['entity_type', 'source_ip', 'geo_location', 'resource_accessed', 
                'auth_method', 'command_sequence', 'device_fingerprint', 'label']
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown')
            
    # Handle numerical columns
    if 'session_duration' in df.columns:
        df['session_duration'] = pd.to_numeric(df['session_duration'], errors='coerce').fillna(0.0)
        
    if 'login_success' in df.columns:
        df['login_success'] = df['login_success'].fillna(False).astype(bool)
        
    # Parse timestamps
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        # Drop rows with invalid timestamps
        df = df.dropna(subset=['timestamp']).copy()
        
    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer new features from the raw data.
    Features: login_hour, day_of_week, session_duration, command_length, 
    unique_resources, failed_login_count, is_known_device, is_known_location.
    """
    logger.info("Engineering features...")
    df = df.copy()
    
    # 1. Time-based features
    if 'timestamp' in df.columns:
        df['login_hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
    else:
        df['login_hour'] = 0
        df['day_of_week'] = 0
        
    # 2. session_duration (Ensure it exists; cleaned in clean_data)
    if 'session_duration' not in df.columns:
        df['session_duration'] = 0.0
        
    # 3. command_length (Estimate length of command sequence if present)
    if 'command_sequence' in df.columns:
        df['command_length'] = df['command_sequence'].apply(
            lambda x: 0 if x in ['N/A', 'Unknown'] else len(str(x).split('->'))
        )
    else:
        df['command_length'] = 0
        
    # 4. unique_resources (Number of resources accessed in the session)
    if 'resource_accessed' in df.columns:
        df['unique_resources'] = df['resource_accessed'].apply(
            lambda x: 0 if x == 'Unknown' else len(str(x).split(','))
        )
    else:
        df['unique_resources'] = 1

    # Need entity_id for history-based features
    has_entity = 'entity_id' in df.columns
    if has_entity:
        # Sort chronologically for historical features
        df = df.sort_values(by=['entity_id', 'timestamp'])
        
        # 5. failed_login_count (Rolling count of failed logins in the last 5 attempts)
        if 'login_success' in df.columns:
            df['is_failed'] = (~df['login_success']).astype(int)
            df['failed_login_count'] = df.groupby('entity_id')['is_failed'].transform(
                lambda x: x.rolling(window=5, min_periods=1).sum()
            )
            df.drop(columns=['is_failed'], inplace=True)
        else:
            df['failed_login_count'] = 0

        # 6. is_known_device (1 if the device was used before by this entity, 0 otherwise)
        if 'device_fingerprint' in df.columns:
            df['device_seq'] = df.groupby(['entity_id', 'device_fingerprint']).cumcount()
            df['is_known_device'] = (df['device_seq'] > 0).astype(int)
            df.drop(columns=['device_seq'], inplace=True)
        else:
            df['is_known_device'] = 1
            
        # 7. is_known_location (1 if the location was used before by this entity, 0 otherwise)
        if 'geo_location' in df.columns:
            df['loc_seq'] = df.groupby(['entity_id', 'geo_location']).cumcount()
            df['is_known_location'] = (df['loc_seq'] > 0).astype(int)
            df.drop(columns=['loc_seq'], inplace=True)
        else:
            df['is_known_location'] = 1
            
        # Restore original index order
        df = df.sort_index()
    else:
        # Fallbacks if entity_id is missing
        df['failed_login_count'] = 0
        df['is_known_device'] = 1
        df['is_known_location'] = 1

    return df

def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode categorical variables using LabelEncoder.
    Produces: auth_method_encoded, entity_type_encoded.
    """
    logger.info("Encoding categorical features...")
    df = df.copy()
    
    le = LabelEncoder()
    
    # Encode auth_method
    if 'auth_method' in df.columns:
        df['auth_method_encoded'] = le.fit_transform(df['auth_method'].astype(str))
        
    # Encode entity_type
    if 'entity_type' in df.columns:
        df['entity_type_encoded'] = le.fit_transform(df['entity_type'].astype(str))
        
    return df

def save_processed_data(df: pd.DataFrame, output_path: str):
    """
    Save the processed DataFrame to a CSV file.
    """
    logger.info(f"Saving processed data to: {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Processed dataset saved successfully.")

def main():
    # Resolve the base directory of the backend (sentinel/backend)
    # __file__ is expected to be at backend/app/ml/feature_engineering.py
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    input_path = os.path.join(base_dir, 'data', 'raw', 'access_logs_raw.csv')
    output_path = os.path.join(base_dir, 'data', 'processed', 'access_logs_processed.csv')
    
    try:
        # 1. Load Data
        df = load_data(input_path)
        
        # 2. Clean Data
        df_clean = clean_data(df)
        
        # 3. Engineer Features
        df_features = engineer_features(df_clean)
        
        # 4. Encode Features
        df_encoded = encode_features(df_features)
        
        # 5. Save Processed Data
        save_processed_data(df_encoded, output_path)
        
        logger.info(f"Feature engineering pipeline completed. Final shape: {df_encoded.shape}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()
