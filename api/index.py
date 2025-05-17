from fastapi import FastAPI
from mangum import Mangum
from app.routes import buses, location, seats, status

app = FastAPI()

app.include_router(buses.router)
app.include_router(location.router)
app.include_router(seats.router)
app.include_router(status.router)

handler = Mangum(app)