from fastapi import APIRouter, HTTPException
from app.firebase import db
from google.cloud.firestore_v1 import GeoPoint
from pydantic import BaseModel
import requests
import os

router = APIRouter(prefix="/buses", tags=["Bus Finder"])

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Set this in your .env or hosting platform

class BusRequest(BaseModel):
    start: str
    destination: str

def get_stop_coordinates(stop_name: str) -> str:
    """Fetch lat,lng string from Firestore stops collection."""
    stop_ref = db.collection("stops").document(stop_name).get()
    if not stop_ref.exists:
        raise HTTPException(status_code=404, detail=f"Stop '{stop_name}' not found in the database")

    stop_data = stop_ref.to_dict()
    location: GeoPoint = stop_data.get("location")
    if not location:
        raise HTTPException(status_code=400, detail=f"Stop '{stop_name}' does not have location data")

    return f"{location.latitude},{location.longitude}"

@router.post("/get")
def get_matching_buses(data: BusRequest):
    start = data.start
    destination = data.destination

    try:
        buses_ref = db.collection("buses").stream()
        matching_buses = []

        for bus_doc in buses_ref:
            bus = bus_doc.to_dict()
            route = bus.get("route", [])
            if start in route and destination in route:
                start_idx = route.index(start)
                end_idx = route.index(destination)

                if start_idx < end_idx and not bus.get("breakdown_status", False):
                    matching_buses.append({
                        "bus_number": bus_doc.id,
                        "number_plate": bus["number_plate"],
                        "reg_mail": bus["reg_mail"],
                        "route": route,
                        "seats_avl": bus["seats_avl"],
                        "current_location": {
                            "lat": bus["current_location"].latitude,
                            "lng": bus["current_location"].longitude
                        }
                    })

        if not matching_buses:
            return {"message": "No matching buses found", "buses": []}

        # Get static destination coordinates from Firestore
        destination_coords = get_stop_coordinates(destination)

        # Add ETA for each bus
        for bus in matching_buses:
            start_coords = get_stop_coordinates(start)
            destination_coords = get_stop_coordinates(destination)

            directions_url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {
                "origin": start_coords,
                "destination": destination_coords,
                "key": GOOGLE_API_KEY
            }
            res = requests.get(directions_url, params=params).json()

            if res["status"] == "OK":
                leg = res["routes"][0]["legs"][0]
                bus["eta"] = leg["duration"]["text"]
                bus["polyline"] = res["routes"][0]["overview_polyline"]["points"]
            else:
                bus["eta"] = "Unavailable"
                bus["polyline"] = None

        return {"buses": matching_buses}

    except HTTPException:
        raise
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail="Something went wrong while processing the request")
