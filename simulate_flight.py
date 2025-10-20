import requests
import time
from datetime import datetime, timezone

API = "http://127.0.0.1:8000/ingest"

FLIGHT_ID = "PK304"
ORIGIN = "LHE"
DESTINATION = "KHI"

lat = 31.5204
lon = 74.3587
altitude = 35000

NUM_PINGS = 15
DELAY = 2

print(f"🛫 Flight {FLIGHT_ID}: {ORIGIN} → {DESTINATION}")
print(f"📡 Sending {NUM_PINGS} GPS pings...\n")

for i in range(NUM_PINGS):
    current_lat = lat - (i * 0.15)
    current_lon = lon - (i * 0.08)
    
    payload = {
        "flight_id": FLIGHT_ID,
        "origin": ORIGIN,
        "destination": DESTINATION,
        "location": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lat": current_lat,
            "lon": current_lon,
            "alt": altitude
        },
        "status": "enroute"
    }
    
    try:
        r = requests.post(API, json=payload)
        if r.status_code == 200:
            print(f"Ping {i+1}/{NUM_PINGS}")
        else:
            print(f"Error: {r.text}")
    except Exception as e:
        print(f"Failed: {e}")
        break
    
    time.sleep(DELAY)

print("\n Landing...")

landing = {
    "flight_id": FLIGHT_ID,
    "location": {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lat": 24.8607,
        "lon": 67.0011,
        "alt": 0
    },
    "status": "landed"
}

try:
    r = requests.post(API, json=landing)
    if r.status_code == 200:
        print(f"✅ {r.json()['message']}")
        print(f"\n Complete!")
        print(f"View: http://127.0.0.1:8000/track/{FLIGHT_ID}")
        print(f" Map: python view_map.py {FLIGHT_ID}")
except Exception as e:
    print(f" Failed: {e}")