import os
from typing import Optional, List

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://analytics_user:analytics_pass@easylink_analytics_db:5432/analytics_db")

SECRET_KEY = os.getenv("SECRET_KEY", "analytics-secret-key-change-in-production")
ALGORITHM = "HS256"

USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://easylink_users_service:8000")
URL_SERVICE_URL = os.getenv("URL_SERVICE_URL", "http://easylink_url_service:8001")

MAX_EXPORT_RECORDS = int(os.getenv("MAX_EXPORT_RECORDS", "100000"))

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin_secret_token_123")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
