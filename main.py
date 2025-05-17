from fastapi import FastAPI
from app.routes import auth
from app.routes import location 
from app.routes import buses
from app.routes import seats
app = FastAPI(title="Transport Management API")

# Include all API routes
app.include_router(auth.router)
app.include_router(location.router)
app.include_router(buses.router)
app.include_router(seats.router)
@app.get("/")
def home():
    return {"message": "Backend is running!"}
