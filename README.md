Flight Tracker API
Overview
A FastAPI-based API for tracking aircraft GPS data using MongoDB. Stores active and completed flights, supports time-based filtering, and includes scripts to simulate flights and visualize paths as interactive maps with Folium.
Requirements

Python 3.8+
MongoDB (local or via MONGODB_URI)
Packages: fastapi, uvicorn, pymongo, requests, folium

Install with pip install fastapi uvicorn pymongo requests folium. Ensure MongoDB is running.
Usage

Start API:
textuvicorn main:app --reload
API runs at http://127.0.0.1:8000.
Simulate Flight:
textpython client.py
Sends 15 GPS pings for flight PK304 (LHE to KHI), ending with a landing ping.
Visualize Path:
textpython view_map.py PK304
Creates PK304_map.html with a polyline, start/end markers, and point details.

API Endpoints

GET /: Lists endpoints.
POST /ingest: Stores GPS data (flight ID, location, status).
GET /track/{flight_id}: Gets flight history; optional at, from_time, to_time filters.
POST /complete/{flight_id}: Archives flight with optional reason.
GET /active: Lists active flights.
GET /completed: Lists completed flights (limit: 50).
GET /search: Filters by origin/destination.

Database
MongoDB with flight_tracker database:

active_flights: Stores ongoing flights (flight ID, path, status, etc.).
completed_flights: Stores archived flights.
Indexes: flight_id (unique on active), origin/destination (compound), flight_id (completed).

Files

main.py: FastAPI app with endpoints and MongoDB logic.
client.py: Simulates flight GPS pings.
view_map.py: Generates HTML map with path and markers.