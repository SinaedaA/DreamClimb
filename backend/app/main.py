## Actual FastAPI app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sectors, problems, circuits, questionnaire

app = FastAPI(title = "DreamClimb API", version = "0.1.0")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dreamclimb.vercel.app",  # Your actual Vercel domain
        "https://*.vercel.app",  # All Vercel preview URLs
        "http://localhost:5173"  # Local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems.router, prefix="/api", tags=["problems"])
app.include_router(sectors.router, prefix="/api", tags=["sectors"])
app.include_router(circuits.router, prefix="/api", tags=["circuits"])
app.include_router(questionnaire.router, prefix="/api", tags=["questionnaire"])

# Test endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the DreamClimb API"}