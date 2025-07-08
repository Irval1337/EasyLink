from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router
from app.database import init_db
from app.config import ALLOWED_ORIGINS

init_db()

app = FastAPI(
    title="EasyLink Auth Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/auth", tags=["auth"])

@app.get("/")
def root():
    return {"message": "EasyLink Auth Service is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
