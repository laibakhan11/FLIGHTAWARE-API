import sys
from pymongo import MongoClient
import folium

client = MongoClient("mongodb://localhost:27017/")
db = client["flight_tracker"]
active = db["active_flights"]
completed = db["completed_flights"]

def get_flight(flight_id):
    flight = active.find_one({"flight_id": flight_id})
    if flight:
        return flight, "active"
    flight = completed.find_one({"flight_id": flight_id})
    if flight:
        return flight, "completed"
    return None, None

def create_map(flight_id):
    flight, source = get_flight(flight_id)
    
    if not flight:
        print(f"Flight {flight_id} not found")
        return
    
    path = flight.get("path", [])
    if not path:
        print(f"No location data")
        return
    
    print(f"Found {flight_id} ({source})")
    print(f"Points: {len(path)}")
    
    first = path[0]
    m = folium.Map([first["lat"], first["lon"]], zoom_start=7)
    
    coords = [(p["lat"], p["lon"]) for p in path]
    folium.PolyLine(coords, color='blue', weight=3).add_to(m)
    
    start = path[0]
    folium.Marker(
        [start["lat"], start["lon"]],
        popup=f"START: {flight.get('origin', '?')}",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)
    
    end = path[-1]
    folium.Marker(
        [end["lat"], end["lon"]],
        popup=f"END: {flight.get('destination', '?')}",
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(m)
    
    for i, p in enumerate(path):
        folium.CircleMarker(
            [p["lat"], p["lon"]],
            radius=4,
            color='blue',
            fill=True,
            popup=f"Point {i+1}<br>{p['timestamp']}<br>Alt: {p['alt']} ft"
        ).add_to(m)
    
    info = f"""
    <div style="position: fixed; bottom: 20px; left: 20px; width: 280px;
                background: white; padding: 15px; border: 2px solid #333;
                border-radius: 8px; z-index: 9999;">
        <h3 style="margin:0 0 10px 0;">Flight {flight_id}</h3>
        <p style="margin:5px 0;"><b>Route:</b> {flight.get('origin', '?')} → {flight.get('destination', '?')}</p>
        <p style="margin:5px 0;"><b>Status:</b> {flight.get('status')}</p>
        <p style="margin:5px 0;"><b>Points:</b> {len(path)}</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(info))
    
    filename = f"{flight_id}_map.html"
    m.save(filename)
    print(f"\nSaved: {filename}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python view_map.py <flight_id>")
        sys.exit(1)
    create_map(sys.argv[1])