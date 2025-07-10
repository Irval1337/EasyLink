from decouple import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = config("DATABASE_URL", default="postgresql://users_user:users_password_123@localhost:5432/users_db")

SECRET_KEY = config("SECRET_KEY", default="super-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_ORIGINS = config("ALLOWED_ORIGINS", default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000").split(",")
