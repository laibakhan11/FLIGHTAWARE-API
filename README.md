## Flight Tracker API
A FastAPI-based API for tracking aircraft GPS data using MongoDB. Stores active and completed flights, supports time-based filtering, and includes scripts to simulate flights and visualize paths with Folium.


## Requirements
Python: 3.8+
MongoDB: Local or via MONGODB_URI
Packages: fastapi, uvicorn, pymongo, requests, folium


## API Endpoints

GET
/
Lists endpoints.


POST
/ingest
Stores GPS data (flight ID, location, status).


GET
/track/{flight_id}
Gets flight history; optional at, from_time, to_time filters.


POST
/complete/{flight_id}
Archives flight with optional reason.


GET
/active
Lists active flights.


GET
/completed
Lists completed flights (limit: 50).


GET
/search
Filters by origin/destination.


## Database:MONGODB
Collections in database:
1. active_flights: Ongoing flights (flight ID, path, status).
Indexes: flight_id (unique), origin/destination (compound).
2.completed_flights: Archived flights.
Index: flight_id.


## Files
main.py: FastAPI app with endpoints and MongoDB logic.
client.py: Simulates flight GPS pings.
view_map.py: Generates HTML map with path and markers.
