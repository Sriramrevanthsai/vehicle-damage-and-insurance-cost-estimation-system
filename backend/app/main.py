import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router
from app.routes.claims import router as claims_router
from app.routes.predict import router as predict_router
from app.services.database import init_db


app = FastAPI(
    title="Vehicle Damage Insurance API",
    description="RT-DETR based vehicle damage detection, severity analysis, and repair cost estimation.",
    version="2.0.0"
)

allowed_origins_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
allow_all_origins = allowed_origins_env.strip() == "*"

# Allow frontend (React) to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else [origin.strip() for origin in allowed_origins_env.split(",")],
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(predict_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(claims_router, prefix="/api")
init_db()


@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "model": "RT-DETR-L custom best.pt",
        "pipeline": ["preprocessing", "damage detection", "severity analysis", "cost estimation"],
    }

@app.get("/api")
def api_health():
    return {
        "status": "ok",
        "model": "RT-DETR-L custom best.pt",
        "pipeline": ["preprocessing", "damage detection", "severity analysis", "cost estimation"],
    }
