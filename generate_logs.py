import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker
from tqdm import tqdm

fake = Faker()

random.seed(42)
np.random.seed(42)
Faker.seed(42)

NUM_USERS = 1000
NUM_DEVICES = 3000
NUM_LOGS = 100000

departments = [
    "Engineering",
    "Finance",
    "HR",
    "IT",
    "Sales",
    "Marketing",
]

roles = [
    "Engineer",
    "Manager",
    "Analyst",
    "Intern",
    "Admin",
]

resources = [
    "Dashboard",
    "Payroll",
    "CRM",
    "Email",
    "Admin",
    "Git",
    "Reports",
]

browsers = [
    "Chrome",
    "Edge",
    "Firefox",
    "Safari",
]

oses = [
    "Windows 11",
    "Ubuntu",
    "macOS",
]

device_types = [
    "Laptop",
    "Desktop",
]

cities = [
    ("Chennai","India",13.08,80.27),
    ("Bengaluru","India",12.97,77.59),
    ("Mumbai","India",19.07,72.87),
    ("Hyderabad","India",17.38,78.48),
    ("Delhi","India",28.61,77.20),
]

users = []

for i in range(NUM_USERS):

    city = random.choice(cities)

    start_hour = random.randint(7,10)

    user = {

        "user_id":f"U{i:05}",

        "username":fake.user_name(),

        "department":random.choice(departments),

        "role":random.choice(roles),

        "city":city[0],

        "country":city[1],

        "lat":city[2],

        "lon":city[3],

        "preferred_browser":random.choice(browsers),

        "preferred_os":random.choice(oses),

        "preferred_start":start_hour,

        "preferred_end":start_hour+8

    }

    users.append(user)

pd.DataFrame(users).to_csv("users.csv",index=False)

devices=[]

for i in range(NUM_DEVICES):

    devices.append({

        "device_id":f"DEV{i:05}",

        "device_type":random.choice(device_types),

        "os":random.choice(oses)

    })

pd.DataFrame(devices).to_csv("devices.csv",index=False)

logs=[]

start=datetime(2026,1,1)

for _ in tqdm(range(NUM_LOGS)):

    user=random.choice(users)

    hour=random.randint(user["preferred_start"],user["preferred_end"])

    minute=random.randint(0,59)

    day=random.randint(0,180)

    ts=start+timedelta(days=day,hours=hour,minutes=minute)

    device=random.choice(devices)

    logs.append({

        "timestamp":ts,

        "user_id":user["user_id"],

        "username":user["username"],

        "department":user["department"],

        "role":user["role"],

        "city":user["city"],

        "country":user["country"],

        "latitude":user["lat"],

        "longitude":user["lon"],

        "device_id":device["device_id"],

        "device_type":device["device_type"],

        "os":user["preferred_os"],

        "browser":user["preferred_browser"],

        "ip":fake.ipv4(),

        "login_success":True,

        "login_method":"Password",

        "resource":random.choice(resources),

        "session_duration":random.randint(5,180),

        "hour":hour,

        "weekday":ts.strftime("%A"),

        "anomaly":0,

        "attack_type":"Normal"

    })

pd.DataFrame(logs).to_csv("access_logs.csv",index=False)

print("Generated 100000 logs.")