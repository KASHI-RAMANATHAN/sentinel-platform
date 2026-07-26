import pandas as pd
import numpy as np
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load the processed access logs data from a CSV file.
    """
    logger.info(f"Loading data from {file_path}")
    try:
        df = pd.read_csv(file_path)
        
        # Map columns if necessary (to support both dataset versions)
        col_mapping = {
            'user_id': 'entity_id',
            'login_method': 'auth_method',
            'resource': 'resource_accessed',
            'device_id': 'device_fingerprint'
        }
        df.rename(columns=col_mapping, inplace=True)
        
        # Create geo_location if missing but city/country exist
        if 'geo_location' not in df.columns and 'city' in df.columns and 'country' in df.columns:
            df['geo_location'] = df['city'] + ", " + df['country']
            
        logger.info(f"Successfully loaded {len(df)} records.")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

def _get_most_frequent(df: pd.DataFrame, group_col: str, target_col: str, new_col_name: str) -> pd.DataFrame:
    """
    Helper function to efficiently find the most frequent value of a target column per group.
    """
    # Count occurrences
    counts = df.groupby([group_col, target_col]).size().reset_index(name='count')
    # Sort by count descending and keep the first (most frequent) per group
    most_freq = counts.sort_values(by='count', ascending=False).drop_duplicates(subset=[group_col])
    # Rename for the final output
    return most_freq[[group_col, target_col]].rename(columns={target_col: new_col_name})

def calculate_login_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate login hour statistics and average daily logins for each entity.
    """
    logger.info("Calculating login patterns...")
    df = df.copy()
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Use login_hour if it exists, otherwise extract from timestamp
    hour_col = 'login_hour' if 'login_hour' in df.columns else df['timestamp'].dt.hour
    
    # Calculate average and standard deviation of login hour
    hour_stats = df.groupby('entity_id')[hour_col].agg(
        average_login_hour='mean',
        login_hour_std='std'
    ).fillna(0).reset_index() # Fill NaNs (e.g. if only 1 login) with 0 for std dev
    
    # Calculate average daily logins
    df['date'] = df['timestamp'].dt.date
    daily_counts = df.groupby(['entity_id', 'date']).size().reset_index(name='daily_logins')
    avg_daily = daily_counts.groupby('entity_id')['daily_logins'].mean().reset_index()
    avg_daily.rename(columns={'daily_logins': 'average_daily_logins'}, inplace=True)
    
    patterns = hour_stats.merge(avg_daily, on='entity_id', how='outer')
    return patterns

def calculate_session_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate average session duration and preferred auth method for each entity.
    """
    logger.info("Calculating session statistics...")
    
    # Average session duration
    duration = df.groupby('entity_id')['session_duration'].mean().reset_index(name='average_session_duration')
    
    # Preferred auth method
    auth = _get_most_frequent(df, 'entity_id', 'auth_method', 'preferred_auth_method')
    
    return duration.merge(auth, on='entity_id', how='outer')

def calculate_preferred_locations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Determine the most frequently used geo-location for each entity.
    """
    logger.info("Calculating preferred locations...")
    return _get_most_frequent(df, 'entity_id', 'geo_location', 'preferred_geo_location')

def calculate_preferred_devices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Determine the most frequently used device fingerprint for each entity.
    """
    logger.info("Calculating preferred devices...")
    return _get_most_frequent(df, 'entity_id', 'device_fingerprint', 'preferred_device')

def calculate_preferred_resources(df: pd.DataFrame) -> pd.DataFrame:
    """
    Determine the most frequently accessed resource for each entity.
    """
    logger.info("Calculating preferred resources...")
    return _get_most_frequent(df, 'entity_id', 'resource_accessed', 'preferred_resource')

def build_user_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Orchestrate the calculation of all behavioral features and merge them into a single profile per entity.
    """
    logger.info("Building user behavior profiles...")
    
    login_patterns = calculate_login_patterns(df)
    session_stats = calculate_session_statistics(df)
    locations = calculate_preferred_locations(df)
    devices = calculate_preferred_devices(df)
    resources = calculate_preferred_resources(df)
    
    # Merge all DataFrames on entity_id
    profiles = login_patterns.merge(session_stats, on='entity_id', how='outer')
    profiles = profiles.merge(locations, on='entity_id', how='outer')
    profiles = profiles.merge(devices, on='entity_id', how='outer')
    profiles = profiles.merge(resources, on='entity_id', how='outer')
    
    return profiles

def save_profiles(df: pd.DataFrame, output_path: str):
    """
    Save the resulting behavioral profiles to a CSV file.
    """
    logger.info(f"Saving profiles to: {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Profiles saved successfully.")

def main():
    # Resolve paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_path = os.path.join(base_dir, 'data', 'processed', 'access_logs_processed.csv')
    output_path = os.path.join(base_dir, 'data', 'processed', 'user_behavior_profiles.csv')
    
    try:
        # Load the processed logs
        df = load_data(input_path)
        
        # Build profiles mapping each entity_id to its baseline behavior
        profiles_df = build_user_profiles(df)
        
        # Save output
        save_profiles(profiles_df, output_path)
        
        logger.info(f"Baseline profiling complete. Extracted {len(profiles_df)} unique entity profiles.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()
