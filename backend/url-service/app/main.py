from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import ALLOWED_ORIGINS, DEBUG, MAX_CUSTOM_URL_LENGTH, SHORT_CODE_LENGTH
from app.database import init_db
from app.api import urls, redirect

app = FastAPI(
    title="EasyLink URL Shortener",
    version="1.0.2",
    debug=DEBUG
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

@app.get("/")
async def root():
    return {"message": "EasyLink URL Shortener Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(urls.router, tags=["URLs"])
app.include_router(redirect.router, tags=["Redirect"])
