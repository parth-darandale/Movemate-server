from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from app.firebase import db, verify_token
from google.cloud.firestore_v1 import GeoPoint

router = APIRouter(prefix="/seats", tags=["Bus Finder"])

# Define the model for seat update
class SeatUpdate(BaseModel):
    seats_avl: int  # Updated number of available seats

# POST endpoint to update available seats
@router.post("/update")
def update_seats(
    seat_update: SeatUpdate, 
    bus_number: str, 
    authorization: str = Header(...)
):
    """Update the available seats for a specific bus"""
    # Verify the token
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
            raise HTTPException(status_code=403, detail="You are not authorized to update this bus's seats")

        # If the email matches, update the available seats
        bus_ref.update({
            "seats_avl": seat_update.seats_avl
        })

        return {"message": "Seats updated successfully"}
    except Exception as e:
        print("Firestore update error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to update seats")

# GET endpoint to retrieve available seats for a specific bus using query parameter
@router.get("/get")
def get_seats(bus_number: str):
    """Retrieve the available seats for a specific bus using query parameter"""
    try:
        # Retrieve the bus document using the bus number as a query parameter
        bus_ref = db.collection("buses").document(bus_number)
        bus_data = bus_ref.get()

        if not bus_data.exists:
            raise HTTPException(status_code=404, detail="Bus not found")

        bus_info = bus_data.to_dict()
        return {"bus_number": bus, "seats_avl": bus_info["seats_avl"]}

    except Exception as e:
        print("Firestore get error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to get seats")
