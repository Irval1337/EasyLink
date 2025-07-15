from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.api.analytics import router as analytics_router
from app.api.admin import admin_router
from app.config import ALLOWED_ORIGINS

app = FastAPI(
    title="Analytics Service",
    version="1.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router, tags=["analytics"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"message": "Analytics Service is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
