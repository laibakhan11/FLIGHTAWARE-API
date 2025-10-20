from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from datetime import datetime, timezone
import os

# Setup
app = FastAPI(title="Flight Tracker API")

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["flight_tracker"]
active = db["active_flights"]
completed = db["completed_flights"]

# Indexes for better performance
active.create_index("flight_id", unique=True)
active.create_index([("origin", 1), ("destination", 1)])
completed.create_index("flight_id")

# Models
class Location(BaseModel):
    timestamp: str
    lat: float
    lon: float
    alt: float = 0

class FlightInput(BaseModel):
    flight_id: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    location: Optional[Location] = None
    status: str = "enroute"

# Helpers
def to_datetime(ts_str: str) -> datetime:
    """Convert ISO timestamp string to datetime object"""
    try:
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        return datetime.fromisoformat(ts_str)
    except:
        raise HTTPException(400, "Invalid timestamp")

def archive_flight(flight_id: str):
    """Move flight from active to completed collection"""
    flight = active.find_one({"flight_id": flight_id})
    if flight:
        completed.insert_one(flight)
        active.delete_one({"flight_id": flight_id})

# Endpoints
@app.get("/")
def home():
    """API home page with available endpoints"""
    return {
        "name": "Flight Tracker API",
        "endpoints": [
            "POST /ingest",
            "GET /track/{flight_id}",
            "POST /complete/{flight_id}",
            "GET /active",
            "GET /completed",
            "GET /search"
        ]
    }

@app.post("/ingest")
def ingest(data: FlightInput):
    """Receive GPS data from aircraft and store in database"""
    if not data.location:
        raise HTTPException(400, "Location required")
    
    point = {
        "timestamp": data.location.timestamp,
        "lat": data.location.lat,
        "lon": data.location.lon,
        "alt": data.location.alt
    }
    
    flight = active.find_one({"flight_id": data.flight_id})
    
    if not flight:
        new_flight = {
            "flight_id": data.flight_id,
            "origin": data.origin,
            "destination": data.destination,
            "status": data.status,
            "started_at": point["timestamp"],
            "last_update": point["timestamp"],
            "path": [point]
        }
        active.insert_one(new_flight)
        msg = f"New flight {data.flight_id} created"
    else:
        active.update_one(
            {"flight_id": data.flight_id},
            {
                "$push": {"path": point},
                "$set": {"last_update": point["timestamp"]}
            }
        )
        msg = f"Location added to {data.flight_id}"
    
    if data.status.lower() == "landed":
        active.update_one(
            {"flight_id": data.flight_id},
            {"$set": {"status": "landed", "ended_at": point["timestamp"]}}
        )
        archive_flight(data.flight_id)
        msg += " - Flight archived"
    
    return {"success": True, "message": msg}

@app.get("/track/{flight_id}")
def track(
    flight_id: str,
    at: Optional[str] = None,
    from_time: Optional[str] = None,
    to_time: Optional[str] = None
):
    """Get flight location history with optional time filtering"""
    flight = active.find_one({"flight_id": flight_id}, {"_id": 0})
    source = "active"
    
    if not flight:
        flight = completed.find_one({"flight_id": flight_id}, {"_id": 0})
        source = "completed"
    
    if not flight:
        raise HTTPException(404, f"Flight {flight_id} not found")
    
    path = flight.get("path", [])
    
    if from_time or to_time:
        filtered = []
        f_from = to_datetime(from_time) if from_time else None
        f_to = to_datetime(to_time) if to_time else None
        
        for p in path:
            p_time = to_datetime(p["timestamp"])
            if f_from and p_time < f_from:
                continue
            if f_to and p_time > f_to:
                continue
            filtered.append(p)
        path = filtered
    
    if at:
        target = to_datetime(at)
        nearest = None
        min_diff = float('inf')
        
        for p in path:
            p_time = to_datetime(p["timestamp"])
            diff = abs((p_time - target).total_seconds())
            if diff < min_diff:
                min_diff = diff
                nearest = p
        
        path = [nearest] if nearest else []
    
    return {
        "flight_id": flight["flight_id"],
        "origin": flight.get("origin"),
        "destination": flight.get("destination"),
        "status": flight.get("status"),
        "started_at": flight.get("started_at"),
        "ended_at": flight.get("ended_at"),
        "source": source,
        "total_points": len(path),
        "path": path
    }


@app.post("/complete/{flight_id}")
def complete(flight_id: str, reason: str = "Manual"):
    """Manually mark a flight as completed and archive it"""
    flight = active.find_one({"flight_id": flight_id})
    
    if not flight:
        if completed.find_one({"flight_id": flight_id}):
            return {"success": True, "message": "Already archived"}
        raise HTTPException(404, "Flight not found")
    
    last_time = flight.get("last_update") or flight.get("started_at")
    active.update_one(
        {"flight_id": flight_id},
        {"$set": {
            "status": "landed",
            "ended_at": last_time,
            "completion_note": reason
        }}
    )
    archive_flight(flight_id)
    
    return {"success": True, "message": f"Flight {flight_id} archived"}

@app.get("/active")
def list_active():
    """List all currently active flights"""
    flights = list(active.find({}, {"_id": 0}))
    return {"count": len(flights), "flights": flights}

@app.get("/completed")
def list_completed(limit: int = 50):
    """List completed flights from log collection"""
    flights = list(completed.find({}, {"_id": 0}).limit(limit))
    return {"count": len(flights), "flights": flights}

@app.get("/search")
def search(
    origin: Optional[str] = None,
    destination: Optional[str] = None
):
    """Search flights by origin and/or destination airport"""
    query = {}
    if origin:
        query["origin"] = origin.upper()
    if destination:
        query["destination"] = destination.upper()
    
    active_results = list(active.find(query, {"_id": 0}))
    completed_results = list(completed.find(query, {"_id": 0}))
    
    return {
        "active": active_results,
        "completed": completed_results,
        "total": len(active_results) + len(completed_results)
    }

