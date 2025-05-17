from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
from app.firebase import db, verify_token

router = APIRouter(prefix="/status", tags=["Breakdown Status"])

class BreakdownUpdate(BaseModel):
    breakdown_status: bool

@router.post("/update")
def update_breakdown_status(
    data: BreakdownUpdate,
    bus_number: str = Query(...),
    authorization: str = Header(...)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    id_token = authorization.split(" ")[1]
    decoded = verify_token(id_token)
    if not decoded:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    user_email = decoded["email"]

    try:
        bus_ref = db.collection("buses").document(bus_number)
        bus_doc = bus_ref.get()

        if not bus_doc.exists:
            raise HTTPException(status_code=404, detail="Bus not found")

        if bus_doc.to_dict()["reg_mail"] != user_email:
            raise HTTPException(status_code=403, detail="Unauthorized")

        bus_ref.update({
            "breakdown_status": data.breakdown_status
        })

        return {"message": f"Breakdown status updated to {data.breakdown_status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get")
def get_breakdown_status(bus_number: str = Query(...)):
    try:
        doc = db.collection("buses").document(bus_number).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Bus not found")

        status = doc.to_dict().get("breakdown_status", False)
        return {"breakdown_status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch breakdown status")
