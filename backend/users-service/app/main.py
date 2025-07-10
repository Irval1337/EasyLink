from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.users import router
from app.database import init_db
from app.config import ALLOWED_ORIGINS

app = FastAPI(
    title="EasyLink Users Service",
    version="1.0.2"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(router, tags=["users"])

@app.get("/")
def root():
    return {"message": "EasyLink Users Service is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
