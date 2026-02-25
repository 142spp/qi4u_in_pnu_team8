from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router as api_router
from .core.loader import load_lectures

app = FastAPI(title="Timetable Optimizer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("Loading lectures into memory...")
    load_lectures()
    print("Lectures loaded successfully!")

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Timetable Optimizer API Context"}
