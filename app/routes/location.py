from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from google.cloud.firestore_v1 import GeoPoint
from app.firebase import db, verify_token

router = APIRouter(prefix="/location", tags=["Bus Location"])

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

@router.post("/update")
def update_location(
    location: LocationUpdate,bus_number: str,
    authorization: str = Header(...)
      # Added bus_number as an argument to specify which bus to update
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    id_token = authorization.split(" ")[1]
    decoded = verify_token(id_token)
    if not decoded:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    user_email = decoded["email"]  # Get the email of the authenticated user

    # Retrieve the bus document to check the email associated with the bus
    try:
        bus_ref = db.collection("buses").document(bus_number)
        bus_data = bus_ref.get()

        if not bus_data.exists:
            raise HTTPException(status_code=404, detail="Bus not found")

        bus_info = bus_data.to_dict()

        # Compare the email of the authenticated driver with the one stored for the bus
        if bus_info["reg_mail"] != user_email:
            raise HTTPException(status_code=403, detail="You are not authorized to update this bus's location")

        # If the email matches, update the location
        bus_ref.update({
            "current_location": GeoPoint(location.latitude, location.longitude)
        })
        return {"message": "Location updated successfully"}
    except Exception as e:
        print("Firestore update error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to update location")

@router.get("/get")
def get_bus_location(bus_number: str):
    try:
        bus_ref = db.collection("buses").document(bus_number)
        bus_data = bus_ref.get()

        if not bus_data.exists:
            raise HTTPException(status_code=404, detail="Bus not found")

        bus_info = bus_data.to_dict()
        current_location = bus_info.get("current_location")

        if not current_location:
            raise HTTPException(status_code=404, detail="Location not available")

        return {
            "bus_number": bus_number,
            "location": {
                "latitude": current_location.latitude,
                "longitude": current_location.longitude
            }
        }

    except Exception as e:
        print("Firestore fetch error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch location")
